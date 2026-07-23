"""
Chile Transparente - Pipeline de Prensa con LLM
Procesa noticias de CIPER, El Mostrador, etc. y extrae información estructurada
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import json
from typing import List, Dict, Optional
from datetime import datetime
import time
from pydantic import BaseModel, Field
from openai import OpenAI
import os


# ============================================================
# SCHEMAS DE DATOS (Pydantic)
# ============================================================

class EntidadImplicada(BaseModel):
    """Persona implicada en el caso."""
    nombre_completo: str
    cargo_o_rol_politico: str = "No especificado"
    partido_politico: str = "No especificado"
    tipo_irregularidad: str
    estado_procesal_mencionado: str
    evidencia_cita_textual: str = Field(
        description="Cita textual exacta del artículo respaldando la implicación"
    )


class EventoEstructurado(BaseModel):
    """Evento/alerta extraído de una noticia."""
    caso_nombre_general: str = Field(
        description="Nombre común del caso (ej: 'Caso SQM', 'Caso Audios')"
    )
    instituciones_involucradas: List[str] = Field(
        default_factory=list,
        description="Ministerios, municipalidades, partidos mencionados"
    )
    entidades_implicadas: List[EntidadImplicada] = Field(
        default_factory=list,
        description="Lista de personas implicadas"
    )
    resumen_caso_corto: str = Field(
        description="Resumen de máximo 3 líneas"
    )
    nivel_de_certeza_extraccion: str = Field(
        description="ALTO, MEDIO o BAJO"
    )
    tipo_alerta: str = Field(
        description="corrupcion | colusion | fraude | cohecho | malversacion | otro"
    )


# ============================================================
# FUENTES DE PRENSA
# ============================================================

class FuentesPrensa:
    """ URLs y configuración de fuentes de prensa chilenas."""
    
    FUENTES = {
        "ciper": {
            "nombre": "CIPER Chile",
            "url": "https://ciperchile.cl",
            "rss": "https://ciperchile.cl/feed/",
            "tags_busqueda": ["corrupción", "fraude", "investigación", "corte", "condena"]
        },
        "mostrador": {
            "nombre": "El Mostrador",
            "url": "https://www.elmostrador.cl",
            "rss": "https://www.elmostrador.cl/feed/",
            "tags_busqueda": ["caso", "investigado", "formalizado", "condena"]
        },
        "biobio": {
            "nombre": "BioBioChile",
            "url": "https://www.biobiochile.cl",
            "rss": "https://www.biobiochile.cl/feed/",
            "tags_busqueda": ["parlamentario", "politico", "caso", "investigacion"]
        },
        "latercera": {
            "nombre": "La Tercera",
            "url": "https://www.latercera.com",
            "rss": "https://www.latercera.com/rss/",
            "tags_busqueda": ["diputado", "senador", "caso", "corrupción"]
        }
    }


# ============================================================
# LECTOR DE FUENTES RSS
# ============================================================

class LectorRSS:
    """Lee feeds RSS de medios de comunicación."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ChileTransparenteBot/1.0)'
        })
    
    def obtener_feed(self, url: str, limite: int = 20) -> List[Dict]:
        """Obtiene artículos del feed RSS."""
        try:
            print(f"  📡 Obteniendo RSS: {url}")
            feed = feedparser.parse(url)
            
            articulos = []
            for entry in feed.entries[:limite]:
                articulos.append({
                    "titulo": entry.get('title', ''),
                    "resumen": entry.get('summary', entry.get('description', '')),
                    "url": entry.get('link', ''),
                    "fecha_publicacion": entry.get('published', ''),
                    "fecha_parsed": entry.get('published_parsed'),
                    "fuente": feed.feed.get('title', url)
                })
            
            print(f"  ✅ {len(articulos)} artículos obtenidos")
            return articulos
            
        except Exception as e:
            print(f"  ❌ Error en RSS: {e}")
            return []
    
    def es_relevante(self, articulo: Dict, politicos: List[str]) -> bool:
        """Verifica si un artículo menciona alguno de los políticos."""
        texto = f"{articulo['titulo']} {articulo['resumen']}".lower()
        
        # Verificar si menciona alguna palabra clave
        palabras_clave = [
            'diputado', 'senador', 'ministro', 'parlamentario',
            'corrupción', 'fraude', 'investigación', 'corte',
            'condena', 'formalizado', 'sobreseído', 'caso'
        ]
        
        tiene_palabra_clave = any(p in texto for p in palabras_clave)
        
        # Verificar si menciona algún político de la lista
        menciona_politico = any(p.lower() in texto for p in politicos)
        
        return tiene_palabra_clave or menciona_politico


# ============================================================
# SCRAPER DE ARTÍCULOS
# ============================================================

class ScraperArticulos:
    """Extrae el contenido completo de artículos de noticias."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def obtener_articulo_completo(self, url: str) -> Optional[Dict]:
        """Obtiene el contenido completo de un artículo."""
        try:
            print(f"  📄 Extrayendo: {url[:80]}...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer título
            titulo = soup.find('h1')
            titulo = titulo.get_text(strip=True) if titulo else ""
            
            # Extraer contenido - selectores comunes
            contenido = ""
            selectors = [
                'article .content', 'article .body', 'article .text',
                '.article-content', '.post-content', '.entry-content',
                'div[itemprop="articleBody"]', 'div[class*="content"]'
            ]
            
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    # Eliminar scripts y estilos
                    for tag in elem.find_all(['script', 'style', 'aside']):
                        tag.decompose()
                    contenido = elem.get_text(separator=' ', strip=True)
                    break
            
            # Si no encontramos contenido, tomar todo el body
            if not contenido:
                body = soup.find('body')
                if body:
                    for tag in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        tag.decompose()
                    contenido = body.get_text(separator=' ', strip=True)
            
            # Limpiar whitespace
            contenido = ' '.join(contenido.split())
            
            # Extraer fecha
            fecha_elem = soup.find(['time', 'span', 'div'], class_=re.compile('date|time|published', re.I))
            fecha = fecha_elem.get_text(strip=True) if fecha_elem else ""
            
            time.sleep(1)  # Rate limiting
            
            return {
                "url": url,
                "titulo": titulo,
                "contenido": contenido[:15000],  # Limitar a 15k caracteres
                "fecha": fecha
            }
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None


import re


# ============================================================
# PROCESADOR LLM
# ============================================================

class ProcesadorLLM:
    """Procesa artículos con LLM para extraer información estructurada."""
    
    PROMPT_SISTEMA = """Eres un Analista de Cumplimiento Normativo y Riesgo Político experto en el sistema legal chileno. 
Tu tarea es leer artículos de prensa y extraer información estructurada sobre personas del ámbito político implicadas 
en irregularidades, investigaciones, colusiones o casos judiciales.

REGLAS ESTRICTAS:
1. Extrae ÚNICAMENTE información explícitamente mencionada en el texto.
2. No uses conocimiento externo ni asumas cargos que no estén en el artículo.
3. Para cada persona, extrae la cita textual exacta que respalda la implicación.
4. Clasifica el estado procesal según los términos del artículo.
5. Si no hay personas implicadas en problemas legales, devuelve lista vacía."""

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
    def procesar_articulo(self, articulo: Dict) -> Optional[EventoEstructurado]:
        """Procesa un artículo y extrae información estructurada."""
        
        prompt_usuario = f"""Procesa esta noticia y extrae información estructurada:

TÍTULO: {articulo['titulo']}

CONTENIDO:
{articulo['contenido']}

URL: {articulo['url']}

Responde SOLO con JSON válido según el schema."""

        try:
            print(f"  🤖 Procesando con LLM...")
            
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.PROMPT_SISTEMA},
                    {"role": "user", "content": prompt_usuario}
                ],
                response_format=EventoEstructurado,
                temperature=0.1  # Baja temperatura para mayor consistencia
            )
            
            resultado = response.choices[0].message.parsed
            
            return {
                "caso_nombre_general": resultado.caso_nombre_general,
                "instituciones_involucradas": resultado.instituciones_involucradas,
                "entidades_implicadas": [e.model_dump() for e in resultado.entidades_implicadas],
                "resumen_caso_corto": resultado.resumen_caso_corto,
                "nivel_de_certeza_extraccion": resultado.nivel_de_certeza_extraccion,
                "tipo_alerta": resultado.tipo_alerta,
                "fuente": {
                    "url": articulo['url'],
                    "titulo": articulo['titulo'],
                    "fecha_procesamiento": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            print(f"  ❌ Error LLM: {e}")
            return None


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================

class PipelinePrensa:
    """Orquesta el pipeline completo de ingestion de prensa."""
    
    def __init__(self):
        self.lector_rss = LectorRSS()
        self.scraper = ScraperArticulos()
        self.procesador_llm = None  # Se inicializa con API key
    
    def ejecutar(
        self, 
        dias_atras: int = 7,
        limite_articulos: int = 50,
        politicos: List[str] = None,
        api_key: str = None
    ) -> List[Dict]:
        """
        Ejecuta el pipeline completo.
        
        Args:
            dias_atras: Buscar artículos de los últimos N días
            limite_articulos: Máximo de artículos a procesar
            politicos: Lista de nombres de políticos a monitorear
            api_key: Clave de API de OpenAI
        """
        
        if api_key:
            self.procesador_llm = ProcesadorLLM(api_key)
        
        resultados = []
        
        # Iterar sobre cada fuente
        for fuente_id, fuente in FuentesPrensa.FUENTES.items():
            print(f"\n📰 Procesando: {fuente['nombre']}")
            
            # Obtener RSS
            articulos = self.lector_rss.obtener_feed(fuente['rss'], limite_articulos)
            
            if not articulos:
                continue
            
            # Filtrar artículos relevantes
            politicos = politicos or []
            articulos_relevantes = [
                a for a in articulos 
                if self.lector_rss.es_relevante(a, politicos)
            ]
            
            print(f"  🔍 {len(articulos_relevantes)} artículos relevantes")
            
            # Procesar cada artículo
            for articulo in articulos_relevantes[:10]:  # Limitar para no exceder cuota
                # Obtener contenido completo
                completo = self.scraper.obtener_articulo_completo(articulo['url'])
                
                if completo and self.procesador_llm:
                    # Procesar con LLM
                    resultado = self.procesador_llm.procesar_articulo(completo)
                    if resultado and resultado.get('entidades_implicadas'):
                        resultados.append(resultado)
                        print(f"    ✅ {resultado['caso_nombre_general']}")
                
                time.sleep(0.5)  # Rate limiting
        
        return resultados
    
    def guardar_resultados(self, resultados: List[Dict], archivo: str = "data/eventos.json"):
        """Guarda los resultados en JSON."""
        import os
        os.makedirs('data', exist_ok=True)
        
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 {len(resultados)} eventos guardados en {archivo}")


def main():
    """Demo del pipeline."""
    print("=" * 60)
    print("Chile Transparente - Pipeline de Prensa")
    print("=" * 60)
    
    # Ejemplo de ejecución (sin LLM para demo)
    print("\n📋 Fuentes configuradas:")
    for fuente_id, fuente in FuentesPrensa.FUENTES.items():
        print(f"  • {fuente['nombre']}: {fuente['url']}")
    
    print("\n" + "=" * 60)
    print("Para ejecutar con LLM:")
    print("  OPENAI_API_KEY=sk-... python 03_pipeline_prensa_llm.py")
    print("=" * 60)
    
    # Guardar schema de ejemplo
    import os
    os.makedirs('data', exist_ok=True)
    
    ejemplo = {
        "pipeline": "Prensa Chile Transparente",
        "fuentes": FuentesPrensa.FUENTES,
        "ejemplo_salida": {
            "caso_nombre_general": "Caso SQM",
            "instituciones_involucradas": ["Ministerio de Minería", "SII"],
            "entidades_implicadas": [
                {
                    "nombre_completo": "M-example politician",
                    "cargo_o_rol_politico": "Senador",
                    "partido_politico": "PS",
                    "tipo_irregularidad": "Financiamiento ilegal",
                    "estado_procesal_mencionado": "Formalizado",
                    "evidencia_cita_textual": "El tribunal determinó que el parlamentario recibió..."
                }
            ],
            "resumen_caso_corto": "Investigación por pagos irregulares de SQM a políticos.",
            "nivel_de_certeza_extraccion": "ALTO",
            "tipo_alerta": "corrupcion",
            "fuente": {
                "url": "https://ciperchile.cl/...",
                "titulo": "Título del artículo",
                "fecha_procesamiento": "2024-01-15T10:30:00"
            }
        }
    }
    
    with open('data/ejemplo_evento.json', 'w', encoding='utf-8') as f:
        json.dump(ejemplo, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Schema de ejemplo guardado en data/ejemplo_evento.json")


if __name__ == "__main__":
    main()
