"""
Chile Transparente - Scraper de Parlamentarios
Extrae la lista de diputados y senadores actuales desde el portal de Datos Abiertos del Congreso de Chile
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
import time


def obtener_diputados_datos_abiertos() -> List[Dict]:
    """
    Obtiene la lista de diputados actuales desde el servicio web de Datos Abiertos del Congreso.
    URL: https://opendata.camara.cl/wspublico/wsdiputados.asmx/retornarDiputadosPeriodoActual
    """
    url = "https://opendata.camara.cl/wspublico/wsdiputados.asmx/retornarDiputadosPeriodoActual"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/xml',
    }
    
    try:
        print("Conectando al portal de Datos Abiertos del Congreso...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        diputados_tags = soup.find_all('Diputado')
        
        lista_diputados = []
        for dip in diputados_tags:
            nombre = dip.find('nombre').text.strip() if dip.find('nombre') else ""
            paterno = dip.find('apellidoPaterno').text.strip() if dip.find('apellidoPaterno') else ""
            materno = dip.find('apellidoMaterno').text.strip() if dip.find('apellidoMaterno') else ""
            
            nombre_completo = f"{nombre} {paterno} {materno}".strip()
            partido = dip.find('partido').text.strip() if dip.find('partido') else "Independiente"
            distrito = dip.find('distrito').text.strip() if dip.find('distrito') else "No especificado"
            
            lista_diputados.append({
                "nombre": nombre_completo,
                "nombre_partes": {"nombre": nombre, "paterno": paterno, "materno": materno},
                "partido": partido,
                "distrito": distrito,
                "tipo": "diputado"
            })
            
        print(f"✓ Se extrajeron {len(lista_diputados)} diputados")
        return lista_diputados
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error de conexión: {e}")
        return []


def obtener_senadores_datos_abiertos() -> List[Dict]:
    """
    Obtiene la lista de senadores actuales desde el servicio web de Datos Abiertos del Congreso.
    URL: https://opendata.camara.cl/wspublico/wssenado.asmx/retornarSenadoresPeriodoActual
    """
    url = "https://opendata.camara.cl/wspublico/wssenado.asmx/retornarSenadoresPeriodoActual"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/xml',
    }
    
    try:
        print("Conectando al servicio de Senadores...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        senadores_tags = soup.find_all('Senador')
        
        lista_senadores = []
        for sen in senadores_tags:
            nombre = sen.find('nombre').text.strip() if sen.find('nombre') else ""
            paterno = sen.find('apellidoPaterno').text.strip() if sen.find('apellidoPaterno') else ""
            materno = sen.find('apellidoMaterno').text.strip() if sen.find('apellidoMaterno') else ""
            
            nombre_completo = f"{nombre} {paterno} {materno}".strip()
            partido = sen.find('partido').text.strip() if sen.find('partido') else "Independiente"
            region = sen.find('region').text.strip() if sen.find('region') else "No especificada"
            
            lista_senadores.append({
                "nombre": nombre_completo,
                "nombre_partes": {"nombre": nombre, "paterno": paterno, "materno": materno},
                "partido": partido,
                "region": region,
                "tipo": "senador"
            })
            
        print(f"✓ Se extrajeron {len(lista_senadores)} senadores")
        return lista_senadores
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error de conexión: {e}")
        return []


def parsear_html_diputados_web() -> List[Dict]:
    """
    Plan B: Extrae diputados desde el HTML visual de la web principal.
    Útil si los datos abiertos no están disponibles.
    """
    url_web = "https://www.camara.cl/diputados/diputados.aspx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        print("Extrayendo desde el sitio web principal...")
        res = requests.get(url_web, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        lista_diputados = []
        
        # Los diputados pueden estar en diferentes estructuras HTML
        # Buscar por múltiples selectores comunes
        tarjetas = soup.find_all('div', class_='g-diputado') or \
                   soup.find_all('li', class_='diputado') or \
                   soup.find_all('div', class_='card-diputado')
        
        for tarjeta in tarjetas:
            nombre_tag = tarjeta.find('h4') or tarjeta.find('h3') or tarjeta.find('span', class_='nombre')
            partido_tag = tarjeta.find('p', class_='partido') or tarjeta.find('span', class_='partido')
            
            if nombre_tag:
                nombre = nombre_tag.text.strip()
                partido = partido_tag.text.strip() if partido_tag else "Independiente"
                
                lista_diputados.append({
                    "nombre": nombre,
                    "partido": partido,
                    "tipo": "diputado",
                    "fuente": "web_scraping"
                })
                
        print(f"✓ Se extrajeron {len(lista_diputados)} diputados desde la web")
        return lista_diputados
        
    except Exception as e:
        print(f"✗ Error en scraping web: {e}")
        return []


def limpiar_nombre_busqueda(nombre: str) -> str:
    """
    Limpia el nombre para búsquedas en bases de datos judiciales.
    Elimina acentos y caracteres especiales.
    """
    import unicodedata
    
    # Normalizar y eliminar acentos
    nombre_limpio = unicodedata.normalize('NFD', nombre)
    nombre_limpio = ''.join(c for c in nombre_limpio if unicodedata.category(c) != 'Mn')
    
    # Eliminar caracteres especiales
    caracteres_especiales = '.,;:\'"()[]{}'
    for char in caracteres_especiales:
        nombre_limpio = nombre_limpio.replace(char, '')
    
    return nombre_limpio.strip().upper()


def generar_lista_para_consulta(politicos: List[Dict]) -> List[Dict]:
    """
    Genera una lista optimizada para consultas en el PJUD.
    Incluye nombres limpios para búsquedas exactas.
    """
    lista_consulta = []
    
    for p in politicos:
        nombre_limpio = limpiar_nombre_busqueda(p['nombre'])
        
        lista_consulta.append({
            "nombre_original": p['nombre'],
            "nombre_busqueda": nombre_limpio,
            "partido": p.get('partido', 'N/A'),
            "distrito": p.get('distrito', p.get('region', 'N/A')),
            "tipo": p.get('tipo', 'N/A'),
            "nombre_partes": p.get('nombre_partes', {})
        })
    
    return lista_consulta


def guardar_json(datos: List[Dict], archivo: str):
    """Guarda los datos en un archivo JSON."""
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print(f"✓ Datos guardados en {archivo}")


def main():
    """Función principal que ejecuta el scraping de todos los parlamentario."""
    print("=" * 60)
    print("Chile Transparente - Scraper de Parlamentarios")
    print("=" * 60)
    print()
    
    # Extraer diputados desde datos abiertos
    print("[1/2] Extrayendo lista de diputados...")
    diputados = obtener_diputados_datos_abiertos()
    
    if not diputados:
        print("  →Intentando método alternativo (web scraping)...")
        diputados = parsear_html_diputados_web()
    
    time.sleep(1)
    
    # Extraer senadores
    print("[2/2] Extrayendo lista de senadores...")
    senadores = obtener_senadores_datos_abiertos()
    
    # Combinar listas
    todos_politicos = diputados + senadores
    
    # Generar versiones para consulta judicial
    lista_consulta = generar_lista_para_consulta(todos_politicos)
    
    # Guardar resultados
    print()
    print("Guardando datos...")
    guardar_json(todos_politicos, 'parlamentarios_raw.json')
    guardar_json(lista_consulta, 'parlamentarios_limpio.json')
    
    # Resumen
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Diputados: {len(diputados)}")
    print(f"Senadores: {len(senadores)}")
    print(f"Total: {len(todos_politicos)}")
    print()
    print("Archivos generados:")
    print("  - parlamentaria_raw.json (datos originales)")
    print("  - parlamentares_limpio.json (para consultas judiciales)")
    
    return todos_politicos


if __name__ == "__main__":
    main()
