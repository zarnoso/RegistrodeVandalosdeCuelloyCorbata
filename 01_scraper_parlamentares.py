"""
Chile Transparente - Scraper de Parlamentares
Extrae la lista completa de diputados y senadores desde fuentes oficiales
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
import time
import re


class ScraperParlamentares:
    """Scraper para extraer datos de diputados y senadores del Congreso de Chile."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def obtener_diputados_datos_abiertos(self) -> List[Dict]:
        """
        Extrae diputados desde el servicio web de Datos Abiertos del Congreso.
        URL: https://opendata.camara.cl/wspublico/wsdiputados.asmx/retornarDiputadosPeriodoActual
        """
        url = "https://opendata.camara.cl/wspublico/wsdiputados.asmx/retornarDiputadosPeriodoActual"
        
        try:
            print("🔗 Conectando al portal de Datos Abiertos del Congreso...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            diputados_tags = soup.find_all('Diputado')
            
            lista_diputados = []
            for dip in diputados_tags:
                # Extraer datos con safe getters
                nombre = self._get_xml_text(dip, 'nombre')
                paterno = self._get_xml_text(dip, 'apellidoPaterno')
                materno = self._get_xml_text(dip, 'apellidoMaterno')
                
                nombre_completo = f"{nombre} {paterno} {materno}".strip()
                
                # Buscar email y otras datos disponibles
                email = self._get_xml_text(dip, 'email') or ""
                
                lista_diputados.append({
                    "nombre_completo": nombre_completo,
                    "nombre_partes": {
                        "nombres": nombre,
                        "apellido_paterno": paterno,
                        "apellido_materno": materno
                    },
                    "partido": self._get_xml_text(dip, 'partido') or "Independiente",
                    "distrito": self._get_xml_text(dip, 'distrito') or "N/A",
                    "region": self._get_xml_text(dip, 'region') or "N/A",
                    "email": email,
                    "cargo": "Diputado",
                    "institucion": "Cámara de Diputados",
                    "periodo": "2022-2026",
                    "es_activo": True,
                    "tipo": "diputado"
                })
                
            print(f"✅ {len(lista_diputados)} diputados extraídos")
            return lista_diputados
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return []
    
    def obtener_senadores(self) -> List[Dict]:
        """
        Extrae senadores desde el sitio web del Senado.
        El Senado no tiene servicio XML público como la Cámara.
        """
        url = "https://www.senado.cl/appsenado/index.php?a=transparencia"
        
        try:
            print("🔗 Conectando al sitio del Senado...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            lista_senadores = []
            
            # Buscar tabla de senadores - selector varía según estructura del sitio
            # Este es un patrón genérico que puede necesitar ajuste
            tablas = soup.find_all('table', class_=re.compile('senadores|parlamentares', re.I))
            
            for tabla in tablas:
                filas = tabla.find_all('tr')
                for fila in filas[1:]:  # Skip header
                    celdas = fila.find_all('td')
                    if len(celdas) >= 3:
                        nombre_completo = celdas[0].get_text(strip=True)
                        partido = celdas[1].get_text(strip=True)
                        region = celdas[2].get_text(strip=True)
                        
                        # Extraer partes del nombre
                        partes = nombre_completo.split()
                        nombres = partes[0] if partes else ""
                        apellidos = partes[1:] if len(partes) > 1 else []
                        
                        lista_senadores.append({
                            "nombre_completo": nombre_completo,
                            "nombre_partes": {
                                "nombres": nombres,
                                "apellido_paterno": apellidos[0] if len(apellidos) > 0 else "",
                                "apellido_materno": " ".join(apellidos[1:]) if len(apellidos) > 1 else ""
                            },
                            "partido": partido,
                            "region": region,
                            "cargo": "Senador",
                            "institucion": "Senado",
                            "periodo": "2022-2030",
                            "es_activo": True,
                            "tipo": "senador"
                        })
            
            if not lista_senadores:
                # Alternativa: buscar por lista de enlaces
                print("  → Buscando en estructura alternativa...")
                links = soup.find_all('a', href=re.compile('senador|parlamentar'))
                print(f"  → {len(links)} enlaces encontrados")
                
            print(f"✅ {len(lista_senadores)} senadores extraídos")
            return lista_senadores
            
        except Exception as e:
            print(f"❌ Error en scraping del Senado: {e}")
            return []
    
    def enriquecem_con_servel(self, politicos: List[Dict]) -> List[Dict]:
        """
        Enriquece los datos con información del SERVEL.
        Busca histórica de candidaturas.
        """
        # Implementación futura: conectas a servel.cl para obtener
        # RUTs, elecciones anteriores, resultados electorales
        
        # Por ahora, generamos RUT ficticio para demo
        for p in politicos:
            if 'rut' not in p:
                # Generar RUTdemo (para testing)
                p['rut'] = self._generar_rut_demo()
                
        return politicos
    
    def _get_xml_text(self, element, tag: str) -> str:
        """Helper seguro para extraer texto de XML."""
        found = element.find(tag)
        return found.text.strip() if found and found.text else ""
    
    def _generar_rut_demo(self) -> str:
        """Genera un RUT de demostración."""
        import random
        num = random.randint(1000000, 25000000)
        dv = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'K']
        return f"{num}-{random.choice(dv)}"
    
    def guardar_json(self, datos: List[Dict], archivo: str):
        """Guarda los datos en un archivo JSON."""
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        print(f"💾 Guardado en {archivo}")


def main():
    """Función principal."""
    print("=" * 60)
    print("Chile Transparente - Scraper de Parlamentares")
    print("=" * 60)
    print()
    
    scraper = ScraperParlamentares()
    
    # Extraer diputados
    print("\n[1/2] Extrayendo Diputados...")
    diputados = scraper.obtener_diputados_datos_abiertos()
    
    # Esperar para no saturar el servidor
    time.sleep(1)
    
    # Extraer senadores
    print("\n[2/2] Extrayendo Senadores...")
    Senado = scraper.obtener_senadores()
    
    # Combinar
    todos = diputados + Senado
    
    # Enriquecer con RUTs demo
    print("\n[3/3] Enriquecendo datos...")
    todos = scraper.enriquecem_con_servel(todos)
    
    # Guardar
    print("\n💾 Guardando datos...")
    scraper.guardar_json(todos, 'data/parlamentares.json')
    
    # Resumen
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Diputados: {len(diputados)}")
    print(f"Senadores: {len(Senado)}")
    print(f"Total: {len(todos)}")
    
    return todos


if __name__ == "__main__":
    import os
    os.makedirs('data', exist_ok=True)
    main()
