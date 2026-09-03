#!/usr/bin/env python3
"""
Script para insertar los 50 senadores de Chile 2022-2026
Fuente: https://www.senado.cl/senadoras-y-senadores/listado-de-senadoras-y-senadores
"""
import os
import psycopg2
import psycopg2.extras

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL no configurada")

# Lista de senadores 2022-2026: (nombre_completo, partido, region, circunscripcion)
SENADORES = [
    ("Pedro Araya Guerrero", "PPD", "Antofagasta", 3),
    ("Danisa Astudillo Peiretti", "PS", "Tarapacá", 2),
    ("Andrea Balladares Letelier", "RN", "Maule", 9),
    ("Miguel Ángel Becker Alvear", "RN", "La Araucanía", 11),
    ("Karim Bianchi Retamales", "Independiente", "Magallanes", 15),
    ("Miguel Ángel Calisto Águila", "Independiente", "Aysén", 14),
    ("Fabiola Campillai Rojas", "Independiente", "Metropolitana", 7),
    ("Karol Cariola Oliva", "PC", "Valparaíso", 6),
    ("Rodolfo Carter Fernández", "Independiente", "La Araucanía", 11),
    ("Loreto Carvajal Ambiado", "PPD", "Ñuble", 16),
    ("Juan Luis Castro González", "PS", "O'Higgins", 8),
    ("Ricardo Celis Araya", "PPD", "La Araucanía", 11),
    ("Daniella Cicardini Milla", "PS", "Atacama", 4),
    ("Luciano Cruz-Coke Carvallo", "Evópoli", "Metropolitana", 7),
    ("Alfonso De Urresti Longton", "PS", "Los Ríos", 12),
    ("Rojo Edwards", "Independiente", "Metropolitana", 7),
    ("Fidel Espinoza Sandoval", "PS", "Los Lagos", 13),
    ("Iván Flores García", "PDC", "Los Ríos", 12),
    ("Camila Flores Oporto", "RN", "Valparaíso", 6),
    ("Sergio Gahona Salazar", "UDI", "Coquimbo", 5),
    ("María José Gatica Bertin", "RN", "Los Ríos", 12),
    ("Francisco Huenchumilla Jaramillo", "PDC", "La Araucanía", 11),
    ("Diego Ibáñez Cotroneo", "Frente Amplio", "Valparaíso", 6),
    ("Vanessa Kaiser Barents-Von Hohenhagen", "Nacional Libertario", "La Araucanía", 11),
    ("Sebastián Keitel Bianchi", "Evópoli", "Biobío", 10),
    ("Alejandro Kusanovic Glusevic", "Independiente", "Magallanes", 15),
    ("Carlos Ignacio Kuschel Silva", "RN", "Los Lagos", 13),
    ("Enrique Lee Flores", "Independiente", "Arica y Parinacota", 1),
    ("Andrés Longton Herrera", "RN", "Valparaíso", 6),
    ("Javier Macaya Danús", "UDI", "O'Higgins", 8),
    ("Vlado Mirosevic Verdugo", "Liberal", "Arica y Parinacota", 1),
    ("Iván Moreira Barros", "UDI", "Los Lagos", 13),
    ("Daniel Núñez Arancibia", "PC", "Coquimbo", 5),
    ("Paulina Núñez Urrutia", "RN", "Antofagasta", 3),
    ("Ximena Ordenes Neira", "Independiente", "Aysén", 14),
    ("Manuel José Ossandón Irarrázabal", "RN", "Metropolitana", 7),
    ("Claudia Pascual Grau", "PC", "Metropolitana", 7),
    ("Yasna Provoste Campillay", "PDC", "Atacama", 4),
    ("Gastón Saavedra Chandía", "PS", "Biobío", 10),
    ("Beatriz Sánchez Muñoz", "Frente Amplio", "Maule", 9),
    ("Gustavo Sanhueza Dueñas", "UDI", "Ñuble", 16),
    ("Alejandra Sepúlveda Orbenes", "Independiente", "O'Higgins", 8),
    ("Arturo Squella Ovalle", "Republicano", "Valparaíso", 6),
    ("Renzo Trisotti Martínez", "Republicano", "Tarapacá", 2),
    ("Ignacio Urrutia Bonilla", "Republicano", "Maule", 9),
    ("Enrique Van Rysselberghe Herrera", "UDI", "Biobío", 10),
    ("Esteban Velásquez Núñez", "FRVS", "Antofagasta", 3),
    ("Cristian Vial Maceratta", "Independiente", "Maule", 9),
    ("Paulina Vodanovic Rojas", "PS", "Maule", 9),
    ("Matías Walker Prieto", "Demócratas", "Coquimbo", 5),
]

# Mapeo de partidos completos
PARTIDO_COMPLETO = {
    "PS": "Partido Socialista",
    "PPD": "Partido por la Democracia",
    "RN": "Renovación Nacional",
    "UDI": "Unión Demócrata Independiente",
    "PDC": "Partido Demócrata Cristiano",
    "PC": "Partido Comunista",
    "Evópoli": "Evópoli",
    "Frente Amplio": "Frente Amplio",
    "Republicano": "Partido Republicano",
    "Nacional Libertario": "Partido Nacional Libertario",
    "Liberal": "Partido Liberal",
    "FRVS": "Federación Regionalista Verde Social",
    "Demócratas": "Demócratas",
    "Independiente": "Independiente",
}

def insertar_senadores():
    conn = psycopg2.connect(DB_URL, sslmode='require')
    cur = conn.cursor()
    
    insertados = 0
    duplicados = 0
    
    for nombre, partido, region, circunscripcion in SENADORES:
        # Verificar si ya existe
        cur.execute("SELECT id FROM politicos WHERE nombre_completo = %s", (nombre,))
        if cur.fetchone():
            duplicados += 1
            continue
        
        partido_completo = PARTIDO_COMPLETO.get(partido, partido)
        
        cur.execute("""
            INSERT INTO politicos (nombre_completo, tipo, region, partido, fuente, fuente_url, created_at, updated_at)
            VALUES (%s, 'senador', %s, %s, 'senado.cl', 'https://www.senado.cl/senadoras-y-senadores/listado-de-senadoras-y-senadores', NOW(), NOW())
        """, (nombre, region, partido_completo))
        insertados += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"✅ Senadores insertados: {insertados}")
    print(f"⏭️  Duplicados omitidos: {duplicados}")
    print(f"📊 Total en lista: {len(SENADORES)}")

if __name__ == "__main__":
    insertar_senadores()
