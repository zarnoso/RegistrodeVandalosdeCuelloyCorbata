# Chile Transparente - Registro de Vándalos de Cuello y Corbata

![Tests](https://github.com/zarnoso/Registro-de-V-ndalos-de-Cuello-y-Corbata/actions/workflows/tests.yml/badge.svg)

**Radar de Transparencia Política - Detectar a los políticos involucrados en corrupción, colusiones y problemas legales.**

## 🚀 Quick Start

```bash
# 1. Clonar
git clone https://github.com/zarnoso/Registro-de-V-ndalos-de-Cuello-y-Corbata.git
cd Registro-de-V-ndalos-de-Cuello-y-Corbata

# 2. Crear .env
cp .env.example .env
# Editar .env con tu DATABASE_URL de Neon

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migración (búsqueda tolerante por nombre)
psql $DATABASE_URL -f scripts/migrations/001_add_pg_trgm_busqueda.sql

# 5. Poblar base de datos
python scripts/populate_database.py

# 6. Ejecutar API
uvicorn app.main:app --reload

# 7. Abrir en navegador
# http://localhost:8000/docs (API docs)
# http://localhost:8000 (Frontend)
```

## 📁 Estructura del Proyecto

```
chile-transparencia/
├── app/
│   ├── api/routes.py          # Endpoints de la API
│   ├── core/
│   │   ├── config.py         # Configuración
│   │   └── database.py       # Conexión a PostgreSQL
│   ├── models/models.py      # Modelos SQLAlchemy
│   ├── schemas/schemas.py    # Schemas Pydantic
│   ├── services/             # Lógica de negocio
│   └── main.py               # FastAPI app
├── scripts/
│   ├── populate_database.py   # Poblar BD con datos
│   └── scraper_chile.py      # Extraer datos reales
├── frontend/
│   └── index.html            # Frontend demo
├── requirements.txt
└── .env
```

## 🧪 Tests

Requiere una Postgres real de test (el esquema usa UUID nativo de Postgres,
incompatible con SQLite) — nunca apunta a la DB de producción.

```bash
pip install -r requirements-dev.txt

# Postgres local desechable para tests (ejemplo)
createdb chile_transparente_test

export TEST_DATABASE_URL="postgresql://usuario:password@localhost:5432/chile_transparente_test"
pytest tests/ -v
```

## 🌐 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/politicos/` | Lista de políticos |
| GET | `/api/politicos/{id}` | Detalle de político |
| GET | `/api/politicos/stats` | Estadísticas |
| GET | `/api/politicos/buscar/rut/{rut}` | Buscar por RUT |
| GET | `/api/politicos/buscar/nombre/{nombre}` | Buscar por nombre (tolerante a typos/tildes) |

## 🗄️ Base de Datos (Neon PostgreSQL)

El proyecto usa **Neon** (PostgreSQL serverless) con las tablas:

- `politicos` - Identidad de autoridades
- `patrimonio` - Declaraciones de patrimonio
- `empresas` - Empresas del político
- `eventos` - Casos legales y alertas
- `familiares` - Red familiar

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
