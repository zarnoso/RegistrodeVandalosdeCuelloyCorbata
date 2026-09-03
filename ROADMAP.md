# Registro de Vándalos de Cuello y Corbata — Roadmap

Nota: este archivo tuvo contenido de otro proyecto del usuario (Google Places,
scraping_jobs, comunas_chile, api.mapata.cl) mezclado por error. Se limpió el
2026-09-02. El detalle completo de cada fix está en `SPEC.md`.

## Arquitectura (confirmada, no tocar sin razón)

- Backend FastAPI en servidor propio, puerto 8006.
- Expuesto vía Cloudflare Tunnel en `api.registrodevandalos.likay.cl`.
- Frontend estático (`frontend/index.html`) en Cloudflare Pages, sin workers ni middleware intermedios.
- Base de datos: Neon (Postgres).

## Completado

| Área | Qué | Cuándo |
|---|---|---|
| Backend | N+1 eliminado en listado, grafo y SOM (JOIN único en vez de cientos de queries) | 2026-09-01/02 |
| Backend | Endpoint de detalle `/api/politicos/{id}` (eventos, familiares, aliases, patrimonio) | 2026-09-01 |
| Backend | Riesgo heredado: familiares con casos suben el `estado_riesgo` del político aunque él no tenga antecedentes propios | 2026-09-01 |
| Backend | Buscador por alias (`/api/buscar/alias/`) | 2026-09-01 |
| Backend | Grafo con familiares como nodos (antes solo leía `relaciones`, vacía) | 2026-09-01 |
| Backend | Tabla y endpoints de `funcionarios_gobierno` (no electos): listado, detalle, filtro por institución | 2026-09-02 |
| Backend | 15 partidos políticos reales poblados; FK `casos_corrupcion.politico_id` agregada (15/128 casos migrados, resto por `ILIKE`) | 2026-09-02 |
| Backend | Tablas `patrimonio`, `pasivos`, `actividades`, `empresas`, `vinculos_empresariales` con datos | 2026-09-02 |
| Frontend | Mojibake corregido en todo el archivo (varias reincidencias) | 2026-09-01/02 |
| Frontend | Rutas relativas → `BACKEND_ORIGIN` centralizado con detección de entorno | 2026-09-01/02 |
| Frontend | Sección "Entorno cercano" en el drawer (familiares + alias + casos de cada uno) | 2026-09-01 |
| Frontend | Buscador de alias conectado al UI (dropdown de coincidencias) | 2026-09-02 |
| Frontend | Vista "Funcionarios" con tarjetas y drawer de detalle | 2026-09-02 |
| Infra | Eliminados 4 archivos de red conflictivos (`_worker.js`, `_middleware.js`, 2× `wrangler.toml`) que apuntaban a 3 dominios/puertos distintos | 2026-09-01 |
| Infra | `.gitignore`, sin credenciales ni `__pycache__`/`.wrangler` en el repo | 2026-09-01 |

## Pendiente — corto plazo (alto impacto, bajo esfuerzo)

| # | Qué | Por qué importa | Bloqueante |
|---|---|---|---|
| 1 | Poblar `relaciones` con datos reales (hoy 0 filas) | el grafo solo muestra familiares; sin esto no hay vínculos amistad/negocios/político visibles | scraping o carga manual |
| 2 | Poblar `noticias_menciones` (hoy 0 filas, salvo pruebas sintéticas) | bloquea el timeline de prensa por persona | pipeline de matching nombre↔noticia |
| 3 | Migrar el resto de `casos_corrupcion` a FK real (113/128 siguen en `NULL`) | el `ILIKE` por nombre es frágil ante homónimos/variaciones de escritura | requiere revisión manual o mejor matching |
| 4 | Hero explicativo en la portada (qué es, para qué sirve, cómo se usa) | primera impresión — hoy el usuario cae directo a la lista sin contexto | ninguno, es solo frontend |
| 5 | Sección "Cómo leer esto" / glosario (qué es alerta roja, qué es riesgo heredado) | evita malas interpretaciones, refuerza el disclaimer legal ya existente | ninguno |

## Pendiente — mediano plazo

| # | Qué | Detalle |
|---|---|---|
| 6 | Grafo interactivo real (d3.js o vis-network) en vez del SVG a mano actual | el actual funciona pero es limitado (max ~70 nodos visibles, sin zoom/pan) |
| 7 | Detectar "conexión no declarada": alias/familiar mencionado en prensa/casos sin fila en `relaciones` | esto es el corazón del objetivo del proyecto — visibilizar a quien "pasa piola" |
| 8 | Timeline interactivo por año (hoy es lista vertical de eventos en el drawer) | mejor lectura de evolución temporal de un caso |
| 9 | Índices `pg_trgm` sobre `casos_corrupcion.responsable` y `familiares.nombre_completo` | el `ILIKE '%x%'` no usa índice normal — con más datos esto degrada el rendimiento |
| 10 | Caché con TTL corto (5-10 min) en `/api/politicos/` | reduce carga a Neon en picos de tráfico, dato no cambia por request |

## Pendiente — largo plazo / escala

| # | Qué | Detalle |
|---|---|---|
| 11 | Scraping automatizado de prensa (CIPER, El Mostrador, BioBioChile) para alimentar `noticias_menciones` | pipeline recurrente, no una carga puntual |
| 12 | Alertas (Telegram u otro canal) cuando aparece un familiar/alias nuevo en prensa de corrupción | proactividad — avisar antes de que la conexión se pierda en el ruido |
| 13 | URLs individuales por político/funcionario (`/perfil/123-nombre`) en vez de todo en un SPA con drawer | mejora indexación SEO y permite compartir un caso puntual |
| 14 | Modo comparación: seleccionar 2-3 personas y ver sus redes combinadas | pedido explícito en `MEJORAS.md`, no implementado aún |
| 15 | Mapa de calor (choropleth) de Chile por densidad de casos, en vez de la vista de barras actual | más intuitivo que "Lectura territorial" actual |

## Notas técnicas activas

- El backend abre una conexión Postgres por endpoint sin `try/finally` — si una query falla a mitad de camino, la conexión queda sin cerrar. No es urgente con el tráfico actual, pero conviene envolver en `try/finally` antes de escalar tráfico.
- `SELECT *` se usa en varios endpoints de `funcionarios_gobierno` — funcional, pero trae columnas sin filtrar; preferible listar columnas explícitas si el schema crece.
- Regla del proyecto: cada push debe agregar una entrada en `SPEC.md` con el detalle de qué cambió y por qué.
