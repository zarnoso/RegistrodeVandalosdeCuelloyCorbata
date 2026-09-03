#!/usr/bin/env python3
"""
Inserta personas clave en casos mediáticos de corrupción en Chile.
Solo figuras extra-parliamentarias (no senadores/diputados actuales o ya cargados).
"""
import os
import psycopg2

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL no configurada")

PERSONAS = [
    # CASO SQM - Financiamiento ilegal a la política
    ("Pablo Longueira Barros", "ex_senador", "UDI", "Metropolitana", "Caso SQM: cohecho, delitos tributarios, absuelto en 2025"),
    ("Marco Enríquez-Ominami", "ex_diputado", "PRO", "Metropolitana", "Caso SQM: 38 facturas falsas a SQM, absuelto en 2025"),
    ("Patricio Contesse González", "empresario", "Independiente", "Metropolitana", "Caso SQM: ex gerente general SQM, mano derecha de Julio Ponce Lerou, absuelto en 2025"),
    ("Cristián Warner Villalobos", "asesor_politico", "Independiente", "Metropolitana", "Caso SQM: ex asesor MEO y secretario PRO, absuelto en 2025"),
    ("Marisol Cavieres Quinteros", "dirigenta_politica", "UDI", "Metropolitana", "Caso SQM: ex secretaria presidencia UDI, absuelta en 2025"),
    ("Carmen Luz Valdivieso", "asesora_politica", "UDI", "Metropolitana", "Caso SQM: ex asesora de Longueira, absuelta en 2025"),
    ("Marcelo Rozas Molina", "funcionario_publico", "DC", "Metropolitana", "Caso SQM: ex embajador en República Checa, asesor de Ponce Lerou, absuelto en 2025"),
    ("Roberto Guzmán Lyon", "abogado", "Independiente", "Metropolitana", "Caso SQM: abogado amigo de Ponce Lerou, facilitación de boletas falsas"),
    ("Julio Ponce Lerou", "empresario", "Independiente", "Metropolitana", "Caso SQM: ex presidente SQM y yerno de Ponce Letelier, accionista controlante"),
    ("Rodrigo Peñailillo Aránguiz", "ex_ministro", "PPD", "Metropolitana", "Caso SQM: ex ministro del Interior de Bachelet, investigación no perseverada"),
    ("Harold Correa Vilches", "asesor_politico", "Independiente", "Metropolitana", "Caso SQM: ex jefe de gabinete ministro Eyzaguirre, investigación no perseverada"),
    ("Alejandro Sule Feliú", "ex_diputado", "RADICAL", "Metropolitana", "Caso SQM: facilitación de boletas falsas, $22 millones desde SQM"),
    ("Clara Bensan Parra", "contadora", "DC", "Metropolitana", "Caso SQM: contadora militante DC, emitió facturas falsas para campaña Frei"),
    ("David Flores Tapia", "asesor_politico", "PPD", "Metropolitana", "Caso SQM: campañas de Carolina Tohá, facturas falsas SQM"),
    ("Juan Marcos Moreno", "funcionario_publico", "PPD", "Metropolitana", "Caso SQM: encargado agenda legislativa Bachelet, boleta falsa SQM $11M"),
    ("Irina Rossi Martínez", "persona_vinculada", "Independiente", "Metropolitana", "Caso SQM: hermana de senador Fulvio Rossi, mencionada en investigación"),
    ("Benjamín Pizarro Soto", "persona_vinculada", "DC", "Metropolitana", "Caso SQM: hijo de ex senador Jorge Pizarro, mencionado en investigación"),
    ("Mariela Molina", "asesora_politica", "PS", "Tarapacá", "Caso SQM: ex asesora de senador Fulvio Rossi, boletas a SQM"),

    # CASO PENTA - Financiamiento ilegal
    ("Carlos Alberto Délano Abbott", "empresario", "Independiente", "Metropolitana", "Caso Penta: dueño de Penta, condenado delitos tributarios, 4 años libertad vigilada"),
    ("Carlos Eugenio Lavín García Huidobro", "empresario", "Independiente", "Metropolitana", "Caso Penta: dueño de Penta, condenado delitos tributarios, 4 años libertad vigilada"),
    ("Hugo Bravo López", "empresario", "Independiente", "Metropolitana", "Caso Penta: ex gerente general Penta III, denunció la trama política, falleció 2017"),
    ("Pablo Wagner Sfeir", "funcionario_publico", "Independiente", "Metropolitana", "Caso Penta: ex subsecretario Minería Piñera, condenado delitos tributarios + enriquecimiento ilícito"),
    ("Manuel Antonio Tocornal Blackburn", "empresario", "Independiente", "Metropolitana", "Caso Penta: gerente general Penta S.A., delitos tributarios"),
    ("Marcos Castro Sanguinetti", "empresario", "Independiente", "Metropolitana", "Caso Penta: ex contador Penta, condenado soborno reiterado 2025"),
    ("Samuel Irarrazaval Comandari", "empresario", "Independiente", "Metropolitana", "Caso Penta: representante legal Penta III, yerno de Délano, delitos tributarios"),
    ("Carlos Bombal Abarca", "asesor_politico", "UDI", "Metropolitana", "Caso Penta: ex senador UDI, asesor Penta, delitos tributarios, sobreseído"),
    ("Iván Álvarez Díaz", "funcionario_publico", "Independiente", "Metropolitana", "Caso Penta: ex fiscalizador SII, condenado 5 años cárcel, fraude al FUT"),
    ("Juan Jesús Martínez Céspedes", "funcionario_publico", "Independiente", "Metropolitana", "Caso Penta: ex fiscalizador SII, cohecho"),
    ("Santiago Valdés Zamora", "funcionario_publico", "Independiente", "Metropolitana", "Caso Penta: ex gerente Bancard, administrador electoral Piñera"),
    ("Isabel Margarita Marinovic", "persona_vinculada", "UDI", "Metropolitana", "Caso Penta: esposa de senador Iván Moreira, suspensión condicional"),
    ("Eduardo Montalva Espinoza", "asesor_politico", "UDI", "Metropolitana", "Caso Penta: ex asesor territorial Moreira, suspendido condicionalmente"),
    ("Andrea Schultz", "asesora_politica", "UDI", "Metropolitana", "Caso Penta: ex secretaria Iván Moreira, suspensión condicional"),
    ("Verónica Nieto", "funcionaria_udia", "UDI", "Metropolitana", "Caso Penta: ex secretaria UDI, suspensión condicional"),
    ("Rodrigo Molina Sotomayor", "persona_vinculada", "UDI", "Metropolitana", "Caso Penta: ex chofer de Iván Moreira, primer boletas falsas que destaparon el caso"),
    ("Carmen Luz de Castro", "asesora_politica", "UDI", "Metropolitana", "Caso Penta/SQM: asesora Zalaquett y campañas Lavín, $5M de SQM"),
    ("María Carolina de la Cerda", "persona_vinculada", "Independiente", "Metropolitana", "Caso Penta/SQM: cuñada de Pablo Wagner, 50 boletas falsas por $120M"),
    ("Alberto Cardemil Bravo", "ex_diputado", "RN", "Metropolitana", "Caso Penta: ex diputado RN, suspendido condicionalmente"),
    ("Andrés Velasco Brañes", "ex_ministro", "Independiente", "Metropolitana", "Caso Penta: ex precandidato presidencial NM, factura empresa $20M, archivo provisional"),
    ("Laurence Golborne Morel", "ex_ministro", "Independiente", "Metropolitana", "Caso Penta: ex ministro Minería Piñera, condenado por boletas falsas $378M, suspensión condicional"),
    ("Carlos Figueroa Serrano", "ex_ministro", "DC", "Metropolitana", "Caso Platas: ex ministro Interior Frei, sociedad recibió $219M de Grupo Angelini"),
    ("Rodrigo Álvarez Zenteno", "ex_diputado", "UDI", "Metropolitana", "Caso Platas: ex ministro Energía, sociedad Seal recibió $22M de Copec"),
    ("Carlos Schultz Fleuriel", "persona_vinculada", "Independiente", "Metropolitana", "Caso Platas: socio de José Silva Bafalluy, $20M por asesorías"),
    ("Ernesto Silva Méndez", "dirigente_politico", "UDI", "Metropolitana", "Caso Penta: ex presidente UDI, hermano de José Silva, mencionado en donaciones Penta"),
    ("Ignacio Ternicier", "periodista", "Independiente", "Metropolitana", "Caso Penta: formalizado delitos tributarios junto a Délano y Lavín"),
    ("Hernán Concha Vial", "asesor_financiero", "Independiente", "Metropolitana", "Caso Penta: asesor financiero Grupo Penta, querellado por contratos forwards"),
    ("Óscar Buzeta Undurraga", "empresario", "Independiente", "Metropolitana", "Caso Penta: gerente Administración y Finanzas Penta, boletas falsas"),
    ("Edgardo Pinto", "empresario", "Independiente", "Metropolitana", "Caso Penta/Cruzat: ejecutivo CB Grupo Cruzat, boletas falsas y delitos tributarios"),
    ("Antonio Espinoza", "empresario", "Independiente", "Metropolitana", "Caso Penta/Cruzat: ejecutivo Forestal Valparaíso, contratos forwards con Penta"),

    # CASO SII/CMF - Caso Audios
    ("Luis Hermosilla Jorche", "abogado", "Independiente", "Metropolitana", "Caso Audios SII/CMF: influyente penalista, soborno a funcionarios SII y CMF, prisión preventiva"),
    ("Daniel Sauer Baffy", "empresario", "Independiente", "Metropolitana", "Caso Audios SII/CMF: controlador Factop y STF, soborno a funcionarios"),
    ("Leonarda Villalobos", "abogada", "Independiente", "Metropolitana", "Caso Audios SII/CMF: co-imputada con Hermosilla, grabó audio, prisión preventiva"),
    ("Luis Angulo", "persona_vinculada", "Independiente", "Metropolitana", "Caso Audios SII/CMF: esposo de Villalobos, arresto domiciliario nocturno"),
    ("Patricio Mejías Esparza", "funcionario_publico", "Independiente", "Metropolitana", "Caso Audios: fiscalizador tributario SII, formalizado por cohecho"),
    ("Renato Robles Iturriaga", "funcionario_publico", "Independiente", "Metropolitana", "Caso Audios: ejecutivo de gestión de cobro TGR, formalizado por cohecho"),

    # CASO LEY FÁRMACOS II
    ("Andrea Martones", "asesora_juridica", "Independiente", "Metropolitana", "Caso Fármacos II: asesora ad-honorem de senadores, cobró $343M de laboratorios mientras asesoría la ley"),

    # CASO TRAMA BIELORRUSA (Vivanco)
    ("Ángela Vivanco Álvarez", "ex_magistrada", "Independiente", "Los Lagos", "Trama Bielorrusa: ex ministra Corte Suprema, cohecho por favorecer a Belaz Movitec contra Codelco, $57M"),
    ("Gonzalo Migueles", "persona_vinculada", "Independiente", "Los Lagos", "Trama Bielorrusa: pareja de Vivanco, receptor de coimas, lavado de activos"),
    ("Eduardo Lagos Munita", "abogado", "Independiente", "Los Lagos", "Trama Bielorrusa: abogado de Belaz Movitec, pagos de coimas, cohecho y lavado"),
    ("Mario Vargas Contreras", "abogado", "Independiente", "Los Lagos", "Trama Bielorrusa: abogado de Belaz Movitec, pagos de coimas, cohecho y lavado"),
    ("Harold Pizarro Iturrieta", "empresario", "Independiente", "Metropolitana", "Trama Bielorrusa: dueño casa de cambio Inversiones Suiza, lavado de activos"),
    ("Sergio Yáber", "funcionario_publico", "Independiente", "Metropolitana", "Trama Bielorrusa: conservador de bienes raíces Puente Alto, lavado de activos"),
    ("Yamil Najle", "funcionario_publico", "Independiente", "Ñuble", "Trama Bielorrusa: conservador de bienes raíces Chillán, lavado de activos"),

    # CASO PAPAYA GATE
    ("Lucía Pinto Pizarro", "ex_intendenta", "UDI", "Coquimbo", "Caso Papaya Gate: ex intendenta, fraude al fisco por compra de terrenos en La Serena por $9.800M"),
    ("José Cáceres", "funcionario_publico", "Independiente", "Coquimbo", "Caso Papaya Gate: ex administrador regional, fraude al fisco"),
    ("Pablo Bracchitta", "empresario", "Independiente", "Coquimbo", "Caso Papaya Gate: gerente inmobiliarias vendedoras, fraude al fisco"),

    # CASO CORPESCA
    ("Enrique Cornejo Gómez", "empresario", "Independiente", "Metropolitana", "Caso Corpesca: pesquera Grupo Angelini, financiamiento irregular"),
    ("Marta Isasi", "ex_diputada", "Independiente", "Antofagasta", "Caso Corpesca: ex diputada, condenada en juicio oral Corpesca"),
    ("Jaime Orpis Bouchon", "ex_senador", "UDI", "Metropolitana", "Caso Corpesca: condenado en juicio oral Corpesca"),

    # FIGURAS CLAVE MENCIONADAS EN INVESTIGACIONES CIPER (boletas tributarias)
    ("Cristián Letelier Aguilar", "funcionario_publico", "UDI", "Metropolitana", "Ministro Tribunal Constitucional: sociedad recibió $22M de Copec, boletas rectificadas"),
    ("Fuad Chahín Arrau", "dirigente_politico", "DC", "Valparaíso", "Presidente DC: mencionado en sentencias tributarias por pagos de boletas"),
    ("Rodolfo Carter Fernández", "alcalde", "UDI", "Metropolitana", "Alcalde La Florida: mencionado en rectificaciones BCI"),
    ("Gustavo Alessandri Rojas", "alcalde", "UDI", "Valparaíso", "Alcalde Zapallar: mencionado en investigaciones de financiamiento"),
    ("Juan Carlos Jobet", "ex_ministro", "Independiente", "Metropolitana", "Ex ministro Energía/Minería Piñera II: mencionado en boletas tributarias"),
]


def run():
    conn = psycopg2.connect(DB_URL, sslmode="require")
    cur = conn.cursor()

    insertados = 0
    duplicados = 0

    for nombre, tipo, partido, region, caso in PERSONAS:
        cur.execute("SELECT id FROM politicos WHERE nombre_completo = %s", (nombre,))
        if cur.fetchone():
            duplicados += 1
            continue

        cur.execute("""
            INSERT INTO politicos
                (nombre_completo, tipo, region, partido, fuente, fuente_url, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, '', NOW(), NOW())
        """, (nombre, tipo, region, partido, f"Caso: {caso[:80]}"))
        insertados += 1

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM politicos WHERE tipo NOT IN ('senador','diputado')")
    total_extra = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM politicos")
    total = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"Insertados: {insertados}")
    print(f"Duplicados omitidos: {duplicados}")
    print(f"Total en lista: {len(PERSONAS)}")
    print(f"DB extra-parliamentarios: {total_extra}")
    print(f"DB total: {total}")


if __name__ == "__main__":
    run()
