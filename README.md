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
psql $DATABASE_URL -f scripts/migrations/002_grafo_fuentes_som.sql

# Estos comandos se ejecutan en una terminal, no en el SQL Editor de Neon.

# 5. Opcional: cargar datos ficticios en una DB local de demo.
# El script borra sus tablas y se niega a operar sobre una DB que no parezca
# de desarrollo/pruebas.
ALLOW_DESTRUCTIVE_DEMO_DATA=true python scripts/populate_database.py

# 6. Ejecutar API
uvicorn app.main:app --reload

# 7. Abrir en navegador
# http://localhost:8000/docs (API docs)
# http://localhost:8000 (Frontend)
```

## 📁 Estructura del Proyecto

```
### Neon SQL Editor

El SQL Editor de Neon acepta únicamente SQL. Ejecuta por separado el contenido de
`scripts/migrations/001_add_pg_trgm_busqueda.sql` y luego
`scripts/migrations/002_grafo_fuentes_som.sql`. No pegues allí comandos `psql`,
`python` ni variables PowerShell como `$env:DATABASE_URL`.

### Despliegue en Vercel

El repositorio incluye `api/index.py` y `vercel.json`, por lo que el frontend y
la API se despliegan juntos. En la pantalla **New Project** usa:

- **Framework preset:** FastAPI
- **Root directory:** `./`
- **Build command:** dejar vacío
- **Output directory:** dejar vacío
- **Environment variable:** `DATABASE_URL` (la cadena de Neon, solo en Vercel)

No agregues `OPENAI_API_KEY` salvo que actives una función que la necesite. La
interfaz usa rutas relativas (`/api`), así que no requiere una URL de backend
separada.

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

La suite puede ejecutarse rápidamente con SQLite o contra una rama PostgreSQL
de pruebas. Nunca utiliza `DATABASE_URL` de producción.

```bash
pip install -r requirements-dev.txt

# Opción rápida y local
export TEST_DATABASE_URL="sqlite:///./data/chile_transparente_test.db"
pytest tests/ -v
```

## 🎬 Demo local completa

La demo usa SQLite y datos 100% ficticios. No necesita cuentas ni claves:

```bash
pip install -r requirements-demo.txt
python scripts/run_demo.py
```

Abre `http://127.0.0.1:8000`. La API, el grafo, las fichas y el SOM funcionan
contra la misma base demo persistente.

En Windows también puedes ejecutar directamente:

```powershell
.\demo.ps1
```

El script crea un entorno aislado la primera vez y luego inicia la demo.

## 🌐 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/politicos/` | Lista de políticos |
| GET | `/api/politicos/{id}` | Detalle de político |
| GET | `/api/politicos/stats` | Estadísticas |
| GET | `/api/politicos/buscar/rut/{rut}` | Buscar por RUT |
| GET | `/api/politicos/buscar/nombre/{nombre}` | Buscar por nombre (tolerante a typos/tildes) |
| GET | `/api/politicos/grafo` | Nodos y relaciones explícitas para el grafo |
| GET | `/api/politicos/analitica/som` | Vectores normalizados para el mapa SOM |
| GET | `/api/fuentes` | Catálogo de fuentes y política de procedencia |

### Recolección oficial a staging

La recolección nunca publica registros automáticamente:

```bash
python scripts/import_fuentes_oficiales.py --dry-run
python scripts/import_fuentes_oficiales.py --source bcn
python scripts/import_fuentes_oficiales.py --source senado
```

Los resultados se guardan en `data/staging_fuentes_oficiales.json` para revisión
humana antes de cualquier importación a la base principal.

### Fuentes judiciales y normativas

- PJUD Transparencia se usa para canales oficiales, sentencias y contraste.
- LeyChile se usa para normativa vigente y contexto jurídico.
- La integración externa de Khipu permanece desactivada hasta contar con
  credenciales, revisión contractual y reglas de protección de datos.
- Ningún resultado judicial se publica sin contraste oficial y revisión humana.

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
