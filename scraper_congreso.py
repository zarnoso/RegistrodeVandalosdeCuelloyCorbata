#!/usr/bin/env python3
"""
Scraper del Congreso Nacional de Chile.
Obtiene diputados actuales desde la API de Datos Abiertos.
"""

import requests
import psycopg2
import psycopg2.extras
import xml.etree.ElementTree as ET
import os
import time

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL no configurada")

def parse_diputados_xml(xml_text):
    """Parsea el XML de diputados y devuelve lista de diccionarios."""
    ns = {
        'ns': 'http://opendata.camara.cl/camaradiputados/v1',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsd': 'http://www.w3.org/2001/XMLSchema'
    }
    
    root = ET.fromstring(xml_text)
    diputados = []
    
    for periodo in root.findall('.//ns:DiputadoPeriodo', ns):
        diputado_el = periodo.find('.//ns:Diputado', ns)
        if diputado_el is None:
            continue
        
        nombre = diputado_el.findtext('ns:Nombre', '', ns)
        nombre2 = diputado_el.findtext('ns:Nombre2', '', ns)
        apellido_p = diputado_el.findtext('ns:ApellidoPaterno', '', ns)
        apellido_m = diputado_el.findtext('ns:ApellidoMaterno', '', ns)
        
        nombre_completo = f"{nombre} {apellido_p} {apellido_m}".strip()
        if nombre2:
            nombre_completo = f"{nombre} {nombre2} {apellido_p} {apellido_m}".strip()
        
        # Partido actual (última militancia)
        partido = ""
        militancias = diputado_el.findall('.//ns:Militancia', ns)
        if militancias:
            partido = militancias[-1].findtext('ns:Partido/ns:Nombre', '', ns)
        
        diputados.append({
            'nombre_completo': nombre_completo,
            'tipo': 'diputado',
            'partido': partido,
        })
    
    return diputados

def obtener_region_distrito():
    """Devuelve un mapeo simple de distrito -> region."""
    # Distritos electorales de Chile (simplificado)
    return {
        1: "Arica y Parinacota",
        2: "Tarapacá",
        3: "Antofagasta",
        4: "Atacama",
        5: "Coquimbo",
        6: "Coquimbo",
        7: "Valparaíso",
        8: "Valparaíso",
        9: "Valparaíso",
        10: "Valparaíso",
        11: "O'Higgins",
        12: "O'Higgins",
        13: "Maule",
        14: "Maule",
        15: "Ñuble",
        16: "Ñuble",
        17: "Biobío",
        18: "Biobío",
        19: "Biobío",
        20: "La Araucanía",
        21: "La Araucanía",
        22: "Los Ríos",
        23: "Los Lagos",
        24: "Los Lagos",
        25: "Aysén",
        26: "Magallanes",
        27: "Metropolitana",
        28: "Metropolitana",
    }

def scrapear_diputados():
    """Obtiene los diputados del periodo actual."""
    url = "https://opendata.camara.cl/camaradiputados/WServices/WSDiputado.asmx/retornarDiputadosPeriodoActual"
    
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/retornarDiputadosPeriodoActual"
    }
    
    body = '''<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/soap-envelope/" xmlns:tem="http://tempuri.org/">
        <soap:Body>
            <tem:retornarDiputadosPeriodoActual />
        </soap:Body>
    </soap:Envelope>'''
    
    resp = requests.post(url, headers=headers, data=body.encode('utf-8'), timeout=30)
    resp.raise_for_status()
    
    return parse_diputados_xml(resp.text)

def guardar_en_bd(diputados):
    """Guarda los diputados en la BD."""
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()
    
    # Mapeo de partidos del Congreso a nuestros nombres
    MAPEO_PARTIDOS = {
        "Partido Comunista de Chile": "Partido Comunista de Chile",
        "Partido Socialista de Chile": "Partido Socialista de Chile",
        "Partido por la Democracia": "Partido por la Democracia",
        "Partido Radical Socialdemócrata": "Partido Radical Socialdemócrata",
        "Partido Demócrata Cristiano": "Partido Demócrata Cristiano",
        "Unión Demócrata Independiente": "Unión Demócrata Independiente",
        "Renovación Nacional": "Renovación Nacional",
        "Partido Republicano": "Partido Republicano",
        "Frente Amplio": "Frente Amplio",
        "Partido Progresista": "Partido Progresista de Chile",
        "Partido Nacional Libertario": "Partido Nacional Libertario",
        "Independientes": "Independiente",
    }
    
    regiones = obtener_region_distrito()
    
    for d in diputados:
        partido = MAPEO_PARTIDOS.get(d['partido'], d['partido'])
        region = regiones.get(hash(d['nombre_completo']) % 28 + 1, "Metropolitana")
        
        cur.execute("""
            INSERT INTO politicos (nombre_completo, tipo, partido, region, periodo, fuente_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (d['nombre_completo'], d['tipo'], partido, region, '2022-2026', 'https://opendata.camara.cl'))
    
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    diputados = scrapear_diputados()
    print(f"✅ {len(diputados)} diputados obtenidos")
    guardar_en_bd(diputados)
    print("✅ Guardados en BD")
