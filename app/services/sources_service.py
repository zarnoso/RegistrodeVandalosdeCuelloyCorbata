"""Catálogo explícito de procedencia y política de ingesta."""

from datetime import datetime, timezone


SOURCES = [
    {
        "id": "camara_datos_abiertos",
        "nombre": "Cámara — Datos Abiertos Legislativos",
        "url": "https://www.camara.cl/transparencia/datosAbiertos.aspx",
        "autoridad": "oficial",
        "prioridad": 1,
        "automatizable": True,
        "formatos": ["XML", "SOAP"],
        "usos": ["identidad", "cargo", "distrito", "partido", "actividad legislativa"],
        "notas": "Fuente primaria. Validar Content-Type: puede responder HTML de mantención.",
    },
    {
        "id": "bcn_resenas",
        "nombre": "BCN — Reseñas biográficas parlamentarias",
        "url": "https://www.bcn.cl/historiapolitica/resenas_parlamentarias/",
        "autoridad": "oficial",
        "prioridad": 1,
        "automatizable": True,
        "formatos": ["HTML"],
        "usos": ["nombre", "biografía", "periodos", "trayectoria parlamentaria"],
        "notas": "Fuente primaria para enriquecimiento histórico; conservar URL de cada reseña.",
    },
    {
        "id": "senado_listado",
        "nombre": "Senado — Listado de senadoras y senadores",
        "url": "https://www.senado.cl/senadoras-y-senadores/listado-de-senadoras-y-senadores",
        "autoridad": "oficial",
        "prioridad": 1,
        "automatizable": True,
        "formatos": ["HTML"],
        "usos": ["identidad", "cargo", "circunscripción", "región", "partido", "comité"],
        "notas": "Fuente primaria vigente; el portal declara 50 integrantes.",
    },
    {
        "id": "servel_historial",
        "nombre": "Servel — Historia de candidatos",
        "url": "https://historial.servel.cl/Candidatos/",
        "autoridad": "oficial",
        "prioridad": 1,
        "automatizable": False,
        "formatos": ["aplicación web"],
        "usos": ["candidaturas", "elecciones", "resultados electorales"],
        "notas": "Portal interactivo. Requiere identificar una interfaz pública estable antes de automatizar.",
    },
    {
        "id": "camara_portal",
        "nombre": "Cámara — Portal institucional",
        "url": "https://www.camara.cl/",
        "autoridad": "oficial",
        "prioridad": 2,
        "automatizable": True,
        "formatos": ["HTML"],
        "usos": ["contraste", "ficha vigente", "actividad legislativa"],
        "notas": "Usar como contraste; preferir Datos Abiertos para ingesta estructurada.",
    },
    {
        "id": "bcn_transparencia",
        "nombre": "BCN — Transparencia activa",
        "url": "https://www.bcn.cl/transparencia/",
        "autoridad": "oficial",
        "prioridad": 3,
        "automatizable": True,
        "formatos": ["HTML", "PDF"],
        "usos": ["normativa", "auditorías", "declaraciones institucionales"],
        "notas": "Describe principalmente a la BCN; no confundir con transparencia de parlamentarios.",
    },
    {
        "id": "pjud_transparencia",
        "nombre": "Poder Judicial — Transparencia",
        "url": "https://www.pjud.cl/transparencia/index",
        "autoridad": "oficial",
        "prioridad": 1,
        "automatizable": False,
        "formatos": ["HTML", "PDF"],
        "usos": ["sentencias", "marco normativo", "estadísticas", "canales oficiales"],
        "notas": (
            "Fuente institucional primaria. El portal enlaza sentencias y consulta "
            "ciudadana, pero esta página no es una API de causas por persona."
        ),
    },
    {
        "id": "bcn_leychile_webservice",
        "nombre": "BCN LeyChile — Legislación abierta",
        "url": "https://www.bcn.cl/leychile/consulta/legislacion_abierta_web_service",
        "autoridad": "oficial",
        "prioridad": 1,
        "automatizable": True,
        "formatos": ["Web Service", "XML", "datos enlazados"],
        "usos": ["normativa", "versiones legales", "vigencia", "contexto jurídico"],
        "notas": (
            "Usar para contextualizar normas y estados legales. No acredita que una "
            "persona sea parte de una causa judicial."
        ),
    },
    {
        "id": "khipu_pjud_causes",
        "nombre": "Khipu API — Causes Per Legal Person",
        "url": "https://docs.khipu.com/apis/v1/cl/services/pjud.cl/openapi/other/causesperlegalperson",
        "autoridad": "externa",
        "prioridad": 2,
        "automatizable": False,
        "requiere_credenciales": True,
        "formatos": ["REST", "OpenAPI"],
        "usos": ["descubrimiento de causas para revisión"],
        "notas": (
            "Integración de tercero. Mantener desactivada hasta validar contrato, "
            "base legal, autenticación, límites y correspondencia con PJUD. Nunca "
            "publicar un resultado sin contraste oficial y revisión humana."
        ),
    },
    {
        "id": "conocelos",
        "nombre": "Conócelos — Diputados",
        "url": "https://conocelos.cl/diputados",
        "autoridad": "secundaria",
        "prioridad": 4,
        "automatizable": False,
        "formatos": ["HTML"],
        "usos": ["contraste editorial"],
        "notas": "Actualmente bloquea acceso automatizado (403). No ingerir sin permiso.",
    },
]


class SourcesService:
    @staticmethod
    def list_sources() -> dict:
        return {
            "fuentes": SOURCES,
            "politica": {
                "publicacion_automatica": False,
                "requiere_fuente_original": True,
                "requiere_revision_humana_para_eventos": True,
                "fuentes_secundarias_solo_contraste": True,
                "apis_externas_requieren_contrato_y_revision": True,
                "causas_requieren_contraste_pjud": True,
            },
            "consultado_en": datetime.now(timezone.utc).isoformat(),
        }
