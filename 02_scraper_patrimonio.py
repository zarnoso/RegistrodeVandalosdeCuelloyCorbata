"""
Chile Transparente - Scraper de Patrimonio
Extrae declaraciones de patrimonio e intereses desde Infoprobidad.cl
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional
import time
import re


class ScraperPatrimonio:
    """Scraper para extraer declaraciones de patrimonio desde Infoprobidad."""
    
    BASE_URL = "https://www.infoprobidad.cl"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8'
        })
    
    def obtener_lista_declaraciones(self, anio: int = 2022) -> List[Dict]:
        """
        Obtiene la lista de declaraciones de patrimonio del año seleccionado.
        Infoprobidad organiza por institución y año.
        """
        # Intentar acceder a la lista de declaraciones
        url = f"{self.BASE_URL}/declaraciones/{anio}"
        
        try:
            print(f"🔗 Conectando a Infoprobidad {anio}...")
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"  → URL directa no disponible, intentando alternativa...")
                # Intentar con parámetros de búsqueda
                url = f"{self.BASE_URL}/buscador?anio={anio}"
                response = self.session.get(url, timeout=15)
            
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            declaraciones = []
            
            # Buscar tablas o listas de declaraciones
            # El selector exacto depende de la estructura actual del sitio
            tablas = soup.find_all('table')
            
            for tabla in tablas:
                filas = tabla.find_all('tr')
                for fila in filas[1:]:  # Skip header
                    celdas = fila.find_all('td')
                    if len(celdas) >= 2:
                        # Extraer link a la declaración individual
                        link_tag = celdas[0].find('a')
                        if link_tag:
                            nombre = link_tag.get_text(strip=True)
                            href = link_tag.get('href', '')
                            
                            if '/declaracion/' in href or '/ver/' in href:
                                declaraciones.append({
                                    "nombre": nombre,
                                    "url": f"{self.BASE_URL}{href}" if not href.startswith('http') else href,
                                    "anio": anio
                                })
            
            print(f"✅ {len(declaraciones)} declaraciones encontradas")
            return declaraciones
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return []
    
    def obtener_detalle_declaracion(self, url: str) -> Optional[Dict]:
        """
        Obtiene el detalle de una declaración individual.
        """
        try:
            print(f"  📄 Obteniendo: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            detalle = {
                "url": url,
                "datos_personales": {},
                "patrimonio": {},
                "empresas": [],
                "acciones": [],
                "bienes_raices": [],
                "intereses": []
            }
            
            # Extraer secciones comunes en Infoprobidad
            # Estos selectores son ejemplos y pueden variar
            
            # 1. Datos del declarante
            nombre_elem = soup.find('h1', class_='nombre-declarante') or \
                        soup.find('h2', class_='nombre') or \
                        soup.find('div', class_='declarante')
            if nombre_elem:
                detalle["datos_personales"]["nombre"] = nombre_elem.get_text(strip=True)
            
            # 2. Buscar tablas de patrimonio
            secciones = soup.find_all(['section', 'div'], class_=re.compile('patrimonio|empresas|acciones|bienes', re.I))
            
            for seccion in secciones:
                titulo = seccion.get('class', [])
                contenido = seccion.get_text(strip=True)
                
                if 'empresa' in ' '.join(titulo).lower():
                    # Extraer empresas de tablas
                    tablas = seccion.find_all('table')
                    for tabla in tablas:
                        filas = tabla.find_all('tr')
                        for fila in filas[1:]:
                            celdas = [c.get_text(strip=True) for c in fila.find_all(['td', 'th'])]
                            if len(celdas) >= 2:
                                detalle["empresas"].append({
                                    "razon_social": celdas[0],
                                    "tipo_sociedad": celdas[1] if len(celdas) > 1 else "",
                                    "rol": celdas[2] if len(celdas) > 2 else "",
                                    "participacion": celdas[3] if len(celdas) > 3 else ""
                                })
            
            # 3. Buscar datos en formato JSON embebido (común en sitios modernos)
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Procesar datos JSON si están estructurados
                    print(f"  → Datos JSON encontrados")
                except:
                    pass
            
            time.sleep(1)  # Rate limiting
            return detalle
            
        except Exception as e:
            print(f"  ❌ Error obteniendo detalle: {e}")
            return None
    
    def mapear_rut_a_patrimonio(self, rut: str) -> Optional[Dict]:
        """
        Busca directamente el patrimonio de una persona por RUT.
        """
        # Infoprobidad puede tener búsqueda por RUT
        url = f"{self.BASE_URL}/declarante/{rut}"
        
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                return self.obtener_detalle_declaracion(url)
            return None
        except:
            return None
    
    def generar_rut_demo(self, nombre: str) -> str:
        """
        Genera un RUTdemo basado en el nombre (para testing).
        """
        import hashlib
        hash_val = int(hashlib.md5(nombre.encode()).hexdigest()[:8], 16)
        dv = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'K']
        rut_num = (hash_val % 25000000) + 1000000
        dv_final = dv[hash_val % 11]
        return f"{rut_num}-{dv_final}"


class EjemploPatrimonio:
    """
    Ejemplo de la estructura de datos de patrimonio que我们需要 generar.
    Esto simula lo que obtendríamos de Infoprobidad.
    """
    
    @staticmethod
    def generar_ejemplos(politicos: List[Dict]) -> List[Dict]:
        """Genera datos de patrimonio de ejemplo para demo."""
        
        empresas_ejemplo = [
            {"razon_social": "Inversiones del Sur Ltda.", "tipo": "Limitada", "rol": "Socio", "participacion": "35%"},
            {"razon_social": "Consultora Valparaíso SpA", "tipo": "SpA", "rol": "Socio", "participacion": "100%"},
            {"razon_social": "Inmobiliaria Manquehue S.A.", "tipo": "S.A.", "rol": "Accionista", "participacion": "5%"},
            {"razon_social": "Constructora Andes Ltda.", "tipo": "Limitada", "rol": "Socio", "participacion": "50%"},
        ]
        
        patrimonio_demo = []
        import random
        
        for politico in politicos[:50]:  # Solo para demo
            num_empresas = random.randint(0, 3)
            empresas = random.sample(empresas_ejemplo, num_empresas)
            
            patrimonio_demo.append({
                "politico_id": politico.get("nombre_completo", ""),
                "rut": f"{random.randint(1000000, 25000000)}-{random.choice(['0','1','2','3','4','5','6','7','8','9','K'])}",
                "periodo": "2022",
                "fuente": "Infoprobidad (simulado)",
                "empresas": empresas,
                "bienes_raices": [
                    {
                        "tipo": "Casa",
                        "comuna": random.choice(["Las Condes", "Providencia", "Vitacura", "Santiago Centro"]),
                        "avaluo": random.randint(50000, 500000) * 100000
                    }
                ] if random.random() > 0.5 else []
            })
        
        return patrimonio_demo


def main():
    """Función principal de demo."""
    print("=" * 60)
    print("Chile Transparente - Scraper de Patrimonio")
    print("=" * 60)
    print()
    
    scraper = ScraperPatrimonio()
    
    # Intentar obtener lista de declaraciones
    print("\n[1/2] Obteniendo lista de declaraciones 2022...")
    declaraciones = scraper.obtener_lista_declaraciones(2022)
    
    if declaraciones:
        # Obtener detalle de los primeros 3 como ejemplo
        print("\n[2/2] Obteniendo detalles de muestra...")
        for decl in declaraciones[:3]:
            detalle = scraper.obtener_detalle_declaracion(decl['url'])
            if detalle:
                print(f"  ✅ {detalle.get('datos_personales', {}).get('nombre', 'N/A')}")
    
    # Guardar ejemplos de estructura
    print("\n💾 Generando ejemplos de estructura de datos...")
    
    import os
    os.makedirs('data', exist_ok=True)
    
    ejemplo = {
        "descripcion": "Estructura de patrimonio según Infoprobidad",
        "campos_esperados": {
            "rut_declarante": "12.345.678-9",
            "nombre_completo": "Nombre Apellido",
            "cargo": "Cargo",
            "institucion": "Institución",
            "periodo_declaracion": "YYYY",
            "patrimonio_total": 0,
            "empresas": [
                {
                    "rut_empresa": "76.XXX.XXX-X",
                    "razon_social": "Nombre Empresa",
                    "tipo_sociedad": "Ltda./SpA/S.A.",
                    "rol": "Socio/Accionista/Director/Representante Legal",
                    "porcentaje_participacion": 0.0,
                    "estado": "Activa/Inactiva"
                }
            ],
            "acciones": [
                {
                    "emisor": "Nombre Bolsa S.A.",
                    "numero_acciones": 0,
                    "porcentaje_total": 0.0
                }
            ],
            "bienes_raices": [
                {
                    "tipo": "Casa/Departamento/Terreno",
                    "comuna": "Nombre Comuna",
                    "avaluo_fiscal": 0,
                    "fecha_adquisicion": "YYYY-MM-DD"
                }
            ],
            "vehiculos": [
                {
                    "marca": "Marca",
                    "modelo": "Modelo",
                    "ano": 2020,
                    "avaluo": 0
                }
            ],
            "deudas": [
                {
                    "tipo": "Hipoteca/Préstamo/Otra",
                    "monto": 0,
                    "acreedor": "Nombre Acreedor"
                }
            ],
        },
        "fuente": "infoprobidad.cl",
        "url_detalle": "https://..."
    }
    
    with open('data/ejemplo_patrimonio.json', 'w', encoding='utf-8') as f:
        json.dump(ejemplo, f, ensure_ascii=False, indent=2)
    
    print("✅ Ejemplo guardado en data/ejemplo_patrimonio.json")
    
    return ejemplo


if __name__ == "__main__":
    main()
