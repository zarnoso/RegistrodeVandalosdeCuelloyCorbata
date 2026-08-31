# Registro de Vándalos de Cuello y Corbata

## Descripción

Plataforma de inteligencia cívica para detectar autoridades chilenas involucradas en corrupción, colusiones y problemas legales.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLOUDFLARE EDGE                             │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────────┐  │
│  │   Pages     │  │   Tunnel    │  │        Workers             │  │
│  │  Frontend   │  │   API       │  │        Proxy               │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬───────────────┘  │
└─────────┼────────────────┼───────────────────────┼──────────────────┘
          │                │                       │
          ▼                ▼                       │
┌──────────────────────────────────────────────────┼──────────────────┐
│                        API                       │                  │
│  ┌───────────────────────────────────────────────┼────────────────┐  │
│  │  GET /api/politicos/                          │                │  │
│  │  GET /api/politicos/{id}                      │                │  │
│  │  GET /api/politicos/grafo                     │                │  │
│  │  GET /api/politicos/analitica/som             │                │  │
│  │  GET /api/buscar/alias/?tipo=X&nombre=Y       │                │  │
│  │  GET /api/relaciones/                         │                │  │
│  │  GET /api/casos/                              │                │  │
│  │  GET /api/noticias/                           │                │  │
│  │  GET /api/stats                               │                │  │
│  └───────────────────────────────────────────────┼────────────────┘  │
└──────────────────────────────────────────────────┼───────────────────┘
                                                   │
                                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        DATABASE (Neon)                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ politicos  │ │   casos    │ │  noticias  │ │ relaciones │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
│  ┌────────────┐ ┌────────────┐                                      │
│  │  aliases   │ │ familiares │                                      │
│  └────────────┘ └────────────┘                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Base de Datos (PostgreSQL)

### Tablas principales

| Tabla | Descripción | Registros |
|---|---|---|
| `politicos` | Autoridades registradas | 289 |
| `casos_corrupcion` | Casos de corrupción | 128 |
| `noticias` | Noticias almacenadas | 260 |
| `relaciones` | Vínculos entre políticos | 0 (pendiente poblar) |
| `politicos_aliases` | Alias (amigo de, hermano de...) | 20 |
| `familiares` | Familiares de políticos | 5 |
| `noticias_menciones` | Menciones de políticos en noticias | 0 |

### Endpoints API

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/politicos/?limit=100` | Lista de políticos |
| GET | `/api/politicos/{id}` | Detalle completo (con aliases, relaciones, casos) |
| GET | `/api/politicos/grafo?limit=250` | Grafo de nodos y aristas |
| GET | `/api/politicos/analitica/som?limit=500` | Vectores SOM |
| GET | `/api/buscar/alias/?tipo=hermano&nombre=X` | Buscar por alias |
| GET | `/api/relaciones/?politico_id=X` | Relaciones de un político |
| GET | `/api/casos/?limit=100` | Casos de corrupción |
| GET | `/api/noticias/?limit=100` | Noticias almacenadas |
| GET | `/api/stats` | Estadísticas del sistema |
| GET | `/health` | Health check |

## Mejoras implementadas (2026-08-31)

### 1. Búsqueda por aliases ✅
- Tabla `politicos_aliases` con tipos: `amigo`, `hermano`, `pareja`, `socio`, `familiar`, `cercano`, `colaborador`
- Permite buscar "amigo de X", "hermano de X", etc.

### 2. Grafo de relaciones ✅
- Tabla `relaciones` con tipos: `familiar`, `amistad`, `negocios`, `político`, `mediatico`
- Endpoint `/api/grafo/` para nodos y aristas

### 3. Noticias con menciones ✅
- Tabla `noticias_menciones` para vincular noticias con políticos
- Endpoint `/api/noticias/` con búsqueda por contenido

### 4. Extracción de entidades (NLP) ✅
- Función `extraer_entidades()` en el backend
- Patrones regex: "X, hermano de Y", "X, amigo de Y", etc.
- Endpoint `/api/extraer-entidades/?texto=X`

## Próximos pasos

1. Poblar tabla `relaciones` con datos reales de infoprobidad
2. Implementar scraper de noticias (CIPER, El Mostrador)
3. Mejorar extracción de entidades con LLM
4. Construir interfaz de administración
5. Implementar sistema de alertas

## Accesos

| Entorno | URL |
|---|---|
| Producción Frontend | https://registrodevandalos.pages.dev |
| Producción API | https://api.registrodevandalos.pages.dev |
| Desarrollo Local | http://localhost:8008 |
| Red Local | http://192.168.100.23:8008 |
