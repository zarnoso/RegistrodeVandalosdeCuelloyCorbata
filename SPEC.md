# Registro de Vándalos de Cuello y Corbata — SPEC.md

## Descripción

Plataforma de inteligencia cívica para detectar autoridades chilenas involucradas en corrupción, colusiones y problemas legales.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLOUDFLARE EDGE                             │
│  ┌─────────────────────────┐  ┌─────────────────────────────────┐  │
│  │   Pages (Frontend)      │  │   Tunnel (Backend)              │  │
│  │   registrodevandalos    │  │   api.registrodevandalos.       │  │
│  │   .pages.dev            │  │   likay.cl                      │  │
│  │                         │  │   → localhost:8006              │  │
│  │   index.html estático   │  │                                 │  │
│  │   con detección de      │  │   FastAPI (Python)              │  │
│  │   entorno               │  │   Puerto 8006                   │  │
│  └─────────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Componentes

### 1. Backend (FastAPI)

| Aspecto | Detalle |
|---|---|
| **Archivo** | `backend.py` |
| **Puerto** | 8006 |
| **Host** | `0.0.0.0` |
| **Base de datos** | Neon PostgreSQL |
| **Túnel** | Cloudflare Tunnel → `api.registrodevandalos.likay.cl` |
| **Cloudflare config** | `~/.cloudflared/config.yml` |

**Endpoints:**

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/politicos/?limit=500&skip=0` | Lista de políticos con datos enriquecidos |
| GET | `/api/politicos/{id}` | Detalle completo (casos, patrimonio, familiares, relaciones, noticias) |
| GET | `/api/politicos/grafo?limit=250` | Grafo de nodos y aristas |
| GET | `/api/politicos/analitica/som?limit=500` | Vectores SOM |
| GET | `/api/casos/?limit=100&skip=0` | Casos de corrupción |
| GET | `/api/stats` | Estadísticas del sistema |
| GET | `/health` | Health check |

**Formato de respuesta de político:**

```json
{
  "id": 697,
  "nombre_completo": "Abraham Gacitúa",
  "tipo": "diputado",
  "region": "Sin región",
  "institucion": "Congreso",
  "cargo": "Diputado",
  "partido": "Partido Liberal Democrático",
  "estado_riesgo": "sin_registros",
  "num_eventos": 0,
  "num_empresas": 0,
  "num_familiares": 0,
  "eventos": [],
  "patrimonios": []
}
```

**Estados de riesgo:**
- `alerta_roja` → más de 2 casos
- `alerta_naranja` → 1-2 casos
- `sin_registros` → 0 casos

---

### 2. Frontend (HTML estático)

| Aspecto | Detalle |
|---|---|
| **Archivo** | `frontend/index.html` |
| **Deploy** | Cloudflare Pages (estático) |
| **URL** | `https://registrodevandalos.pages.dev` |
| **Dependencias** | Ninguna (HTML vanilla + CSS + JS) |

**Detección automática de entorno:**

```javascript
const _isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.hostname === "192.168.100.23" || location.port === "8006";
const API_BASE = _isLocal ? "/api/politicos" : "https://api.registrodevandalos.likay.cl/api/politicos";
const API_CASES = _isLocal ? "/api/casos" : "https://api.registrodevandalos.likay.cl/api/casos";
```

**Reglas:**
- NO usar `_worker.js` ni `_middleware.js` en Pages
- NO crear Workers proxy
- El HTML decide la URL del backend según `location.hostname`
- Local usa rutas relativas `/api/politicos`
- Producción usa URL absoluta `https://api.registrodevandalos.likay.cl/api/politicos`

---

### 3. Base de Datos (Neon PostgreSQL)

**Tablas principales:**

| Tabla | Descripción | Registros |
|---|---|---|
| `politicos` | Autoridades registradas | 289 |
| `casos_corrupcion` | Casos de corrupción | 128 |
| `noticias` | Noticias almacenadas | 260 |
| `relaciones` | Vínculos entre políticos | 4 |
| `politicos_aliases` | Alias (amigo de, hermano de...) | 20 |
| `familiares` | Familiares de políticos | 15 |
| `noticias_menciones` | Menciones de políticos en noticias | 0 |

**Columnas de `politicos`:**

| Columna | Tipo | Descripción |
|---|---|---|
| id | integer | PK |
| nombre_completo | varchar | Nombre completo |
| nombre | varchar | Nombre |
| apellido_paterno | varchar | Apellido paterno |
| apellido_materno | varchar | Apellido materno |
| email | varchar | Email |
| tipo | varchar | Tipo (diputado, senador, investigado) |
| region | varchar | Región |
| periodo | varchar | Período parlamentario |
| fuente | varchar | Fuente de datos |
| datos_json | jsonb | Datos adicionales |
| partido | varchar | Partido político |
| created_at | timestamp | Fecha de creación |
| updated_at | timestamp | Fecha de actualización |
| fuente_url | text | URL de la fuente |
| fecha_extraccion | timestamp | Fecha de extracción |
| fecha_verificacion | timestamp | Fecha de verificación |

---

## Infraestructura

### Cloudflare Tunnel

**Configuración (`~/.cloudflared/config.yml`):**

```yaml
tunnel: 654da129-237a-4b8a-a4c2-89601ed61e88
credentials-file: /home/chumbeke/.cloudflared/654da129-237a-4b8a-a4c2-89601ed61e88.json

ingress:
  - hostname: api.mapadata.cl
    service: http://localhost:8001
  - hostname: api.registrodevandalos.likay.cl
    service: http://localhost:8006
  - service: http_status:404
```

**DNS:**

| Registro | Tipo | Contenido | Proxy |
|---|---|---|---|
| api.mapadata.cl | CNAME | 654da129-237a-4b8a-a4c2-89601ed61e88.cfargotunnel.com | ON |
| api.registrodevandalos.likay.cl | CNAME | 654da129-237a-4b8a-a4c2-89601ed61e88.cfargotunnel.com | ON |
| registrodevandalos.likay.cl | CNAME | registrodevandalos.pages.dev | ON |

### Cloudflare Pages

| Aspecto | Detalle |
|---|---|
| Proyecto | `registrodevandalos` |
| Dominio | `registrodevandalos.pages.dev` |
| Dominio personalizado | `registrodevandalos.likay.cl` |
| Build command | (ninguno, estático) |
| Output directory | `frontend/` |

---

## Desarrollo Local

### Requisitos

- Python 3.11+
- Neon PostgreSQL
- Cloudflare Tunnel (cloudflared)

### Variables de entorno

```bash
DATABASE_URL="postgresql://neondb_owner:***@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
```

### Iniciar backend

```bash
cd /home/chumbeke/registro-devandalos
source /home/chumbeke/esphome-venv/bin/activate
python -m uvicorn backend:app --host 0.0.0.0 --port 8006
```

### Iniciar túnel

```bash
cloudflared tunnel run mapadata
```

### Acceder

- Frontend + API: `http://localhost:8006`
- API pública: `https://api.registrodevandalos.likay.cl`

---

## Despliegue

### Backend (systemd)

```bash
systemctl --user restart registro-devandalos.service
```

### Frontend (Cloudflare Pages)

```bash
cd /home/chumbeke/registro-devandalos
CLOUDFLARE_API_TOKEN=*** npx wrangler pages deploy frontend/ --project-name registrodevandalos --branch main
```

---

## Archivos del proyecto

```
registro-devandalos/
├── backend.py              # FastAPI backend (puerto 8006)
├── frontend/
│   └── index.html          # Frontend estático (Cloudflare Pages)
├── README.md               # Documentación
├── ROADMAP.md              # Roadmap del proyecto
└── SPEC.md                 # Este archivo
```

**Archivos que NO deben existir:**
- ❌ `frontend/_worker.js` — No usar Workers en Pages
- ❌ `frontend/_middleware.js` — No usar middleware en Pages
- ❌ `proxy-wrangler.toml` — No usar proxy workers
- ❌ Cualquier otro backend (solo `backend.py`)

---

## Reglas importantes

1. **Un solo backend**: Solo `backend.py` en puerto 8006
2. **Un solo dominio de API**: `api.registrodevandalos.likay.cl`
3. **No Workers en Pages**: El frontend es HTML estático puro
4. **Detección automática**: El HTML decide la URL del backend según el hostname
5. **No hardcodeo de credenciales**: Usar variables de entorno
6. **CORS abierto**: `allow_origins=["*"]` para permitir cross-origin
7. **No mezclar proyectos**: Mapata (puerto 8001) y Registro Vándalos (puerto 8006) son independientes

---

## Próximos pasos

1. Poblar más partidos políticos con datos reales
2. Implementar scraping de noticias (CIPER, El Mostrador)
3. Crear tabla de relaciones con datos reales
4. Mejorar extracción de entidades con NLP
5. Implementar sistema de alertas

---

## Changelog

### 2026-09-01 — Fix backend/frontend: N+1, detalle, riesgo heredado, alias, limpieza

**Backend (`backend.py`):**
- Eliminada credencial Neon hardcodeada — ahora requiere `DATABASE_URL` sin default.
- N+1 corregido: `listar_politicos` pasó de ~870 queries (3 por cada uno de 289 políticos) a 1 query con `LEFT JOIN` agregado.
- Agregado endpoint `/api/politicos/{id}` (detalle): trae eventos, familiares, aliases y patrimonios reales.
- Agregado endpoint `/api/buscar/alias/`: búsqueda por apodo, no solo nombre legal.
- Riesgo heredado: nueva función `calcular_riesgo_heredado()` — suma casos propios + 0.5×casos de familiares directos, así el entorno de un político con antecedentes queda visible aunque él no tenga casos propios.
- `partido` ya no está hardcodeado a "Sin partido" — se lee de la columna real de `politicos`.

**Frontend (`frontend/index.html`):**
- Corregido mojibake (36+ ocurrencias, reincidente 2 veces por sobrescritura externa): texto guardado con doble encoding UTF-8→Latin-1→UTF-8. Validado en 0 residuos al cierre.
- Bug funcional: comparaciones `.includes("en_revisin")` sin tilde nunca matcheaban contra `"en_revisión"` real de la BD — estados procesales se clasificaban mal. Corregido en 2 puntos.
- Nueva sección "Entorno cercano" en el drawer: muestra familiares y alias de cada político, con flag visual cuando un familiar tiene casos de corrupción a su propio nombre.

**Limpieza de infraestructura:**
- Eliminados `_worker.js`, `frontend/_worker.js`, `frontend/functions/api/_middleware.js`, `wrangler.toml`, `proxy-wrangler.toml` — 4 configuraciones de red conflictivas apuntando a 3 dominios/puertos distintos (`localhost:8005`, `api.mapadata.cl`, `registro.mapadata.cl`), ninguna coordinada con el Cloudflare Tunnel real.
- Eliminado `__pycache__/` y `.wrangler/cache/` del control de versiones (exponía email y account ID de Cloudflare). Agregado `.gitignore`.

**Próximos pasos (agregado a la lista existente):**
6. Poblar tabla `noticias_menciones` para timeline unificado por persona.
7. Detectar "conexión no declarada": alias/familiar mencionado en prensa/casos sin fila correspondiente en `relaciones`.
