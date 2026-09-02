# Catastro de Mejoras — Registro de Vándalos

## 📊 Estado Actual del Proyecto

| Componente | Estado |
|---|---|
| Backend FastAPI | ✅ Puerto 8006, caché, paginación |
| Frontend HTML estático | ✅ Filtros, diseño moderno |
| Base de datos Neon | ✅ 289 políticos, 128 casos |
| Cloudflare Pages | ✅ Deployado |
| Cloudflare Tunnel | ✅ api.registrodevandalos.likay.cl |

---

## 🎨 Mejoras Visuales y de UX (Prioridad Alta)

### 1. Cómo mostrar la idea de forma más entendible

| Mejora | Descripción | Impacto |
|---|---|---|
| **Hero con explicación clara** | Sección inicial que explique QUÉ es el proyecto, PARA QUÉ sirve, y CÓMO usarlo en 3 pasos | Muy alto |
| **Guía de uso interactiva** | Tour paso a paso para nuevos usuarios (Usa Shepherd.js o similar) | Alto |
| **Tarjetas de historias reales** | Mostrar casos destacados como "Caso Y" → "Político X vinculado a Z" | Alto |
| **Visualización de red grafo** | Mostrar relaciones visualmente (d3.js o vis-network) | Alto |
| **Línea temporal interactiva** | Timeline visual por año con casos | Medio |
| **Mapa de calor por regiones** | Choropleth de Chile con densidad de casos | Medio |

### 2. Hacer la página más bonita

| Mejora | Descripción |
|---|---|
| **Animaciones suaves** | Transiciones entre vistas, hover en tarjetas |
| **Dark mode** | Toggle para modo oscuro |
| **Imágenes de políticos** | Fotos desde Wikipedia/BCN |
| **Iconografía consistente** | Iconos SVG para cada tipo de relación |
| **Tipografía jerárquica** | Uso de Newsreader/DM Mono más marcado |
| **Microinteracciones** | Feedback visual al hacer clic, cargar, filtrar |

### 3. Hacerlo más didáctico

| Mejora | Descripción |
|---|---|
| **Sección "¿Cómo leer esto?"** | Explicación de cada campo, colores, estados |
| **Ejemplos guiados** | "Ejemplo: Busca a un diputado de la RM con alerta roja" |
| **Tooltips informativos** | Ayuda contextual en cada elemento |
| **Glosario** | Definir términos (¿Qué es alerta roja? ¿Qué es patrimonio?) |
| **Comparador** | Seleccionar 2-3 políticos y comparar sus redes |
| **Historias de_periodistas** | Sección con reportajes basados en los datos |

---

## 🚀 Catastro de Mejoras Técnicas

### A. Backend

| Mejora | Prioridad | Esfuerzo |
|---|---|---|
| **Cache con Redis** | Alta | Medio (usar Upstash Redis gratis) |
| **Rate limiting** | Alta | Bajo (slowapi ya usado en Mapata) |
| **Endpoint de búsqueda por alias** | Alta | Bajo |
| **Endpoint /api/relaciones/red/{id}** | Media | Medio (grafo 2do grado) |
| **Compresión gzip** | Media | Bajo |
| **Caché de endpoints con ETag** | Bajo | Bajo |
| **Health check detallado** | Bajo | Bajo |
| **Swagger/OpenAPI docs** | Bajo | Ya incluido en FastAPI |

### B. Frontend

| Mejora | Prioridad | Esfuerzo |
|---|---|---|
| **Filtro por partido** | Alta | ✅ YA IMPLEMENTADO |
| **Filtro por rango de fechas** | Media | Medio |
| **Grafo interactivo** | Alta | Alto (d3.js) |
| **Mapa de calor Chile** | Media | Medio |
| **Timeline horizontal** | Media | Medio |
| **Modo comparación** | Media | Alto |
| **URLs individuales por político** | Bajo | Medio (requiere router) |
| **Paginación infinita** | Bajo | Bajo |
| **Lazy load de detalle** | Bajo | ✅ YA IMPLEMENTADO |

### C. Base de Datos

| Mejora | Prioridad | Esfuerzo |
|---|---|---|
| **Índices compuestos** | Alta | Bajo |
| **Full-text search** | Media | Medio (tsvector) |
| **Tabla de correcciones_pendientes** | Bajo | Bajo |
| **Tabla de fuentes** | Bajo | Bajo |
| **Auditoría de cambios** | Bajo | Bajo |

### D. Infraestructura

| Mejora | Prioridad | Esfuerzo |
|---|---|---|
| **CI/CD automático** | Media | Bajo (GitHub Actions) |
| **Monitoreo de uptime** | Bajo | Bajo |
| **Alertas de caída** | Bajo | Bajo |
| **Backup automático BD** | Bajo | Bajo |

---

## 📥 Fuentes de Datos y Cómo Obtenerlas

### A. Datos que YA tenemos

| Fuente | Datos | Cantidad | Actualización |
|---|---|---|---|
| Wikipedia | Políticos históricos, partidos | 289 | Estática |
| BCN (Biblioteca Congreso) | Reseñas biográficas | 289 | Estática |
| Casos de corrupción (manual) | Casos documentados | 128 | Manual |

### B. Datos que podemos SCRAPEAR

| Fuente | Datos | Método | Prioridad |
|---|---|---|---|
| **CIPER** | Investigaciones, noticias | Scraping + Firecrawl | Alta |
| **El Mostrador** | Noticias de corrupción | Scraping + Firecrawl | Alta |
| **BioBioChile** | Noticias regionales | Scraping + Firecrawl | Alta |
| **La Tercera** | Noticias nacionales | Scraping + Firecrawl | Media |
| **Emol** | Noticias | Scraping | Media |
| **infoprobidad.cl** | Declaraciones de patrimonio | Scraping | Alta |
| **SII** | Datos de empresas | API + Scraping | Media |
| **Diario Oficial** | Nombramientos, resoluciones | Scraping | Media |
| **SERVEL** | Cargos electos | Scraping | Media |
| **ChileCompra** | Licitaciones, contrataciones | API + Scraping | Alta |
| **Ley del Lobby** | Reuniones, regalos | Scraping | Alta |
| **Transparencia Activa** | Datos de gobierno | API | Media |

### C. Datos de APIs públicas

| API | Datos | URL | Prioridad |
|---|---|---|---|
| **API Congreso** | Diputados, senados, leyes | congreso.cl/api | Alta |
| **API SII** | Empresas, RUTs | sii.cl/api | Media |
| **API ChileCompra** | Licitaciones | mercadopublico.cl | Alta |
| **API Datos Abiertos** | Datos gobierno | datos.gob.cl | Media |

### D. Datos de LLM/Investigación

| Fuente | Método | Prioridad |
|---|---|---|
| **Perplexity AI** | Búsqueda + síntesis | Alta |
| **Firecrawl** | Scraping inteligente | Alta |
| **GPT-4/Claude** | Extracción de entidades | Media |
| **Google News API** | Noticias | Media |
| **Wikipedia API** | Datos biográficos | Baja |

### E. Estrategia de Población de Datos

| Prioridad | Fuente | Método | Herramienta |
|---|---|---|---|
| 1 | CIPER | Scraping programático | Firecrawl + cron |
| 2 | El Mostrador | Scraping programático | Firecrawl + cron |
| 3 | infoprobidad.cl | Scraping manual + cron | Scrapy |
| 4 | ChileCompra | API | requests |
| 5 | Ley del Lobby | Scraping | Scrapy |
| 6 | SII | API + scraping | requests |
| 7 | BCN | Scraping biografías | BeautifulSoup |
| 8 | Wikipedia API | API | requests |

---

## 📋 Plan de Acción Recomendado

### Sprint 1 (Esta semana): UX/Visual
1. ✅ Agregar filtros por partido, región, riesgo
2. ✅ Mejorar diseño responsive
3. ✅ Agregar hero explicativo
4. ✅ Agregar sección "¿Cómo leer esto?"
5. ✅ Mejorar tarjetas de políticos

### Sprint 2 (Próxima semana): Grafo + Noticias
1. Implementar grafo interactivo (d3.js)
2. Crear scraper de CIPER (Firecrawl)
3. Crear scraper de El Mostrador (Firecrawl)
4. Poblar noticias_menciones con datos reales

### Sprint 3 (2 semanas): Datos masivos
1. Scraping de infoprobidad.cl (patrimonio)
2. Integrar API ChileCompra
3. Poblar relaciones con datos reales
4. Implementar timeline interactivo

### Sprint 4 (1 mes): Funcionalidades avanzadas
1. Modo comparación de políticos
2. Mapa de calor de Chile
3. URLs individuales por político
4. Sistema de alertas Telegram

---

## 📊 Cómo Mostrar la Información a la Gente

### Opción A: Dashboard Ejecutivo (Recomendada)

**Página principal:**
1. **Hero**: "289 autoridades · 128 casos documentados · Vínculos ocultos revelados"
2. **Stats**: 4 tarjetas grandes (políticos, casos, relaciones, regiones)
3. **Filtros**: Buscar, partido, región, riesgo
4. **Lista**: Tarjetas de políticos con avatares de colores
5. **Detalle**: Panel lateral con toda la info del político seleccionado

### Opción B: Historias/Narrativa

**Página principal:**
1. **Historias destacadas**: "Caso Hermagoras" · "Caso Paco Horts" · "Caso Yovana Ahumada"
2. **Buscador**: "Busca tu comuna, político o partido"
3. **Mapa de Chile**: Clic en región → ver políticos
4. **Grafo**: Red visual de relaciones

### Opción C: Periodismo de Datos

**Página principal:**
1. **Investigaciones**: Reportajes basados en los datos
2. **Datos abiertos**: "Descarga los datos"
3. **Metodología**: "¿Cómo verificamos la información?"
4. **API**: "Accede vía API"

---

## 🎯 Recomendación Final

**Combinar Opción A + B:**
- Dashboard principal con stats y filtros (A)
- Sección de "Casos destacados" (B)
- Footer con metodología y enlaces a datos abiertos

---

## 📁 Archivos de Referencia

| Archivo | Contenido |
|---|---|
| `frontend/index.html` | Frontend actual |
| `backend.py` | Backend actual |
| `ROADMAP.md` | Roadmap técnico |
| `SPEC.md` | Especificación de arquitectura |
| `MEJORAS.md` | Este archivo |
