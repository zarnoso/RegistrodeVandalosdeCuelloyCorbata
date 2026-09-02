# Registro de Vándalos — Roadmap

## Estado actual (2026-09-01)

### Completado

| Tarea | Fecha |
|---|---|
| Frontend Next.js básico | 2026-08-26 |
| Frontend profesional UX/UI | 2026-08-26 |
| Backend FastAPI (endpoints) | 2026-08-26 |
| Worker Google Places | 2026-08-26 |
| Tabla `scraping_jobs` en Neon | 2026-08-26 |
| Tabla `comunas_chile` (347 comunas) | 2026-08-28 |
| API endpoints funcionales | 2026-08-26 |
| Worker loop con `FOR UPDATE SKIP LOCKED` | 2026-08-26 |
| Extracción de emails desde webs | 2026-08-26 |
| Deduplicación de resultados | 2026-08-26 |
| Generación de CSV | 2026-08-26 |
| Bucket R2 creado | 2026-08-27 |
| Token R2 configurado | 2026-08-27 |
| Backend corriendo en systemd | 2026-08-27 |
| Worker corriendo en systemd | 2026-08-27 |
| Token eliminado del historial de git | 2026-08-28 |
| Repo GitHub limpio (sin secretos) | 2026-08-28 |
| Cloudflare Tunnel creado | 2026-08-28 |
| Registro DNS `api.mapata.cl` | 2026-08-28 |
| Backend accesible vía tunnel | 2026-08-28 |
| Google Places API Key configurada | 2026-08-28 |
| Worker procesando jobs | 2026-08-28 |
| DNS de DonWeb apuntando a Cloudflare | 2026-08-28 |
| Auditoría de seguridad backend | 2026-08-28 |
| Rate limiting + headers de seguridad | 2026-08-28 |
| Frontend deployado en Cloudflare Pages | 2026-08-28 |
| **Worker v5.0 — Mejoras de conciliación y rendimiento** | 2026-08-31 |
| **Frontend v2 con filtros y diseño moderno** | 2026-09-01 |
| **Backend v3 con caché, paginación y FK** | 2026-09-01 |
| **Columna partido en Neon DB** | 2026-09-01 |
| **Índices pg_trgm para búsquedas** | 2026-09-01 |
| **Noticias con menciones** | 2026-09-01 |
| **Relaciones por partido** | 2026-09-01 |

### Mejoras del Worker v5.0

| Mejora | Estado |
|---|---|
| 1. ThreadPoolExecutor con lock para DDG (thread-safe) | ✅ |
| 2. Checkpointing incremental por zona (resume tras caída) | ✅ |
| 3. Pool de conexiones + reconexión automática Neon | ✅ |
| 4. Dedup en SQL (memoria acotada) | ✅ |
| 5. Errores informativos en DB (traceback) | ✅ |
| 6. Graceful shutdown con signal handling | ✅ |
| 7. Upload real a R2 (S3-compatible) | ✅ |
| 8. Config validation al inicio (fail-fast) | ✅ |
| 9. Health check endpoint | ✅ |
| 10. Circuit breaker para Places API | ✅ |
| 11. Enriquecimiento paralelizado (3 workers) | ✅ |
| 12. Batch writes (cada 50 zonas) | ✅ |
| 13. Límite de jobs concurrentes (2) | ✅ |
| 14. Alertas Telegram en fallo | ✅ |
| 15. Stale job detector (5 min) | ✅ |

---

## Próximos pasos (pendientes)

### Fase 2: Sistema de Relaciones y Noticias

| Mejora | Descripción | Estado |
|---|---|---|
| **1. Búsqueda por aliases** | Tabla de relaciones: "amigo de", "hermano de", "pareja de", "socio de" para detectar vínculos en búsquedas | ⏳ Pendiente |
| **2. Scraping de noticias** | Buscar en CIPER, El Mostrador, BioBioChile menciones de políticos | ⏳ Pendiente |
| **3. Extracción de entidades** | NLP/regex para detectar nombres de políticos en textos de noticias | ⏳ Pendiente |
| **4. Grafo de relaciones** | Conectar políticos con sus redes (familiares, empresas, socios) en el grafo | ⏳ Pendiente |

### Detalle de mejoras:

#### 1. Búsqueda por aliases
- Crear tabla `politicos_aliases` con: `politico_id`, `alias_tipo` (amigo, hermano, socio, etc.), `alias_nombre`, `fuente_url`
- Endpoint: `/api/politicos/buscar/alias/{tipo}/{nombre}`
- Ejemplo: `/api/politicos/buscar/alias/hermano/JuanPerez` → devuelve políticos relacionados

#### 2. Scraping de noticias
- Scrapers de CIPER, El Mostrador, BioBioChile, La Tercera
- Buscar menciones: "amigo de [político]", "hermano de [político]", "cercano a [político]"
- Almacenar en tabla `noticias_menciones` con: `noticia_id`, `politico_id`, `tipo_mencion`

#### 3. Extracción de entidades
- Regex para detectar: "X, hermano de Y", "X, amigo de Y", "X, socio de Y"
- O usar LLM para extracción de entidades en noticias
- Vincular menciones con políticos registrados

#### 4. Grafo de relaciones
- Tabla `relaciones` con: `politico_origen_id`, `politico_destino_id`, `tipo_relacion` (familiar, amistad, negocios, etc.), `fuente_url`
- Endpoint: `/api/politicos/grafo?incluir_relaciones=true`
- Visualizar en el frontend: nodos conectados por aristas de colores según tipo

---

## En progreso

| Tarea | Estado | Notas |
|---|---|---|
| Implementar aliases de políticos | ⏳ | En cola |
| Scraping de noticias con menciones | ⏳ | En cola |
| Extracción de entidades NLP | ⏳ | En cola |
| Grafo de relaciones | ⏳ | En cola |

---

## Próximos pasos inmediatos

1. **Implementar búsqueda por aliases** (tabla + endpoint)
2. **Agregar scraping de noticias** (CIPER, El Mostrador)
3. **Crear tabla de relaciones** (familiares, socios, amigos)
4. **Actualizar grafo** para mostrar relaciones

---

## Notas técnicas

- El worker usa `FOR UPDATE SKIP LOCKED` para concurrencia
- Google Places API tiene límite de 60 resultados por query
- Se recomienda no exceder 2000 queries por job (costo ~$34 USD)
- Los CSVs se generan con UTF-8 BOM para compatibilidad con Excel
- El sistema respeta rate limits de Google (2s entre páginas, 0.1s entre detalles)
- El backend corre en Python 3.11 (evita problemas con psycopg2 en 3.13)
- El worker v5.0 incluye: paralelización, checkpointing, circuit breaker, batch writes
- Health check endpoint: http://localhost:8002/health
- Alertas Telegram configurables vía `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`
