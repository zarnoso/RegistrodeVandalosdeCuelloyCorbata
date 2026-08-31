# Registro de Vándalos — Roadmap

## Estado actual (2026-08-31)

### Completado

| Tarea | Fecha |
|---|---|
| Frontend "Trama Pública" (Codex) | 2026-08-31 |
| Backend adaptador (FastAPI) | 2026-08-31 |
| Conexión a Neon DB (datos existentes) | 2026-08-31 |
| Cloudflare Pages deploy | 2026-08-31 |
| Cloudflare Tunnel (API) | 2026-08-31 |
| **1. Búsqueda por aliases** | 2026-08-31 |
| **2. Grafo de relaciones** | 2026-08-31 |
| **3. Noticias con menciones** | 2026-08-31 |
| **4. Extracción de entidades (NLP)** | 2026-08-31 |

### Detalle de mejoras implementadas:

#### 1. Búsqueda por aliases ✅
- Tabla `politicos_aliases` creada
- Tipos: `amigo`, `hermano`, `pareja`, `socio`, `familiar`, `cercano`, `colaborador`, `otro`
- Función SQL `buscar_por_alias(tipo, nombre)`
- Endpoint: `/api/buscar/alias/?tipo=hermano&nombre=X`
- Ejemplo: `/api/buscar/alias/?tipo=amigo&nombre=perez`

#### 2. Grafo de relaciones ✅
- Tabla `relaciones` creada con tipos: `familiar`, `amistad`, `negocios`, `político`, `mediatico`, `otro`
- Endpoint: `/api/grafo/` para nodos y aristas
- Endpoint: `/api/relaciones/?politico_id=X` para relaciones de un político
- Visualización en el frontend: grafo SVG interactivo

#### 3. Noticias con menciones ✅
- Tabla `noticias_menciones` creada para vincular noticias con políticos
- Endpoint: `/api/noticias/?busqueda=X` busca en título, contenido y políticos mencionados
- Endpoint: `/api/noticias/{id}` muestra noticia con sus menciones
- Tabla `familiares` para relaciones familiares documentadas

#### 4. Extracción de entidades (NLP simple) ✅
- Función Python `extraer_entidades(texto)` con regex
- Patrones detectados:
  - "X, hermano de Y" → tipo: familiar
  - "X, amigo de Y" → tipo: amistad
  - "X, socio de Y" → tipo: negocios
  - "X, pareja de Y" → tipo: pareja
- Endpoint: `/api/extraer-entidades/?texto=X`

### Datos actuales

| Tabla | Registros |
|---|---|
| politicos | 289 (200 diputados, 79 senadores, 10 investigados) |
| casos_corrupcion | 128 |
| noticias | 260 |
| politicos_aliases | 20 |
| familiares | 5 |
| relaciones | 0 (pendiente poblar con datos reales) |
| noticias_menciones | 0 (pendiente poblar) |

---

## Próximos pasos (pendientes)

| Tarea | Prioridad | Descripción |
|---|---|---|
| Poblar relaciones | 🔴 Alta | Extraer vínculos de infoprobidad.cl |
| Scraper de noticias | 🟡 Media | CIPER, El Mostrador, BioBioChile |
| NLP avanzado | 🟡 Media | Usar LLM para extracción de entidades |
| Admin dashboard | 🟢 Baja | Interfaz para administrar datos |
| Alertas | 🟢 Baja | Notificar nuevos casos |

---

## Notas técnicas

- Backend: Python 3.11+ con FastAPI
- Base de datos: Neon (PostgreSQL)
- Frontend: HTML vanilla + CSS + JS (sin framework)
- Cloudflare Pages para frontend estático
- Cloudflare Tunnel para API
- Diseño: "Trama Pública" (tipografía Manrope/Newsreader/DM Mono)
- Colores: Verde teal (#087f73), azul cobalto (#315aa8), ámbar (#d18a23)
