# Chile Transparente - Radar de Transparencia Política

**Plataforma citizen-tech para monitorear problemas legales, patrimonio y conflictos de interés de políticos chilenos.**

## 🎯 Visión

Crear un "dossier público" de cada político chileno - quién es, qué empresas tiene, qué problemas legales ha tenido, y qué dicen los medios. Una herramienta de fiscalización ciudadana automatizada que hoy no existe de manera unificada.

## 📁 Estructura del Proyecto

```
chile-transparencia/
│
├── SPEC.md                           # Especificación técnica completa
├── README.md                         # Este archivo
│
├── frontend/
│   └── index.html                   # Página web completa (demo)
│
├── scripts/
│   ├── 01_scraper_parlamentares.py  # Extrae diputados/senadores del Congreso
│   ├── 02_scraper_patrimonio.py     # Extrae declaraciones de Infoprobidad
│   └── 03_pipeline_prensa_llm.py    # Pipeline de prensa con LLM
│
└── data/                            # Datos extraídos (generados)
```

## 🔧 Componentes

### 1. Scraper de Parlamentares
Extrae la lista completa de diputados y senadores desde:
- **Portal de Datos Abiertos** (opendata.camara.cl) - XML
- **Sitio del Senado** (senado.cl) - HTML

### 2. Scraper de Patrimonio
Extrae declaraciones de patrimonio e intereses desde:
- **Infoprobidad.cl** - Declaraciones juradas
- **Infolobby.cl** - Reuniones con lobbistas

### 3. Pipeline de Prensa con LLM
Procesa noticias automáticamente para detectar implicaciones de políticos:
- **CIPER Chile** - Periodismo de investigación
- **El Mostrador** - Noticias políticas
- **BioBioChile** - Noticias generales

## 🚀 Cómo Empezar

```bash
# Instalar dependencias
pip install requests beautifulsoup4 lxml feedparser openai pydantic

# Extraer dados
python scripts/01_scraper_parlamentares.py

# Abrir frontend
open frontend/index.html
```

## 📊 Fuentes de Datos

| Tipo | Fuente |
|------|--------|
| Identidad | Cámara/Senado (opendata.camara.cl) |
| Patrimonio | Infoprobidad (infoprobidad.cl) |
| Prensa | CIPER, El Mostrador, BioBioChile |
| Judicial | PJUD (pjud.cl) |

## ⚠️ Consideraciones Legales

1. **Solo fuentes públicas**
2. **Derecho de rectificación** para políticos
3. **Sin juicios de valor** - Solo hechos verificables
4. **Atribución clara** a fuentes originales

---

**Chile Transparente** - Construyendo transparencia política para Chile 🇨🇱
