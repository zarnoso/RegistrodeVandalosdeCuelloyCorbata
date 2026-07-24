# Chile Transparente - Especificación Técnica

## Visión del Producto

**Nombre:** Chile Transparente (o "RadarPol")

**Misión:** Armar un "dossier público" de cada político chileno - quién es, qué empresas tiene, qué problemas legales ha tenido, y qué dicen los medios de él/ella.

**Modelo Mental:** Como un "LinkedIn de transparencia" - una ficha completa por persona que cualquiera pueda consultar.

---

## Modelo de Datos (Arquitectura)

### Entidad 1: `politicos`
```json
{
  "id": "uuid",
  "rut": "12.345.678-5",
  "nombre_completo": "Juan Pérez García",
  "nombre_partes": {
    "nombres": "Juan",
    "apellido_paterno": "Pérez",
    "apellido_materno": "García"
  },
  "fecha_nacimiento": "1980-05-15",
  "foto_url": "https://...",
  
  // Datos políticos
  "cargo_actual": "Diputado",
  "institucion": "Cámara de Diputados",
  "partido": "Partido Socialista",
  "coalicion": "Nuevo Pacto Social",
  "distrito": "Distrito 10",
  "region": "Metropolitana",
  "periodo_actual": "2022-2026",
  "es_activo": true,
  
  // Metadatos
  "fuente_oficial": "SERVEL/Cámara",
  "fecha_primera_candidatura": "2009",
  "creado_en": "timestamp",
  "actualizado_en": "timestamp"
}
```

### Entidad 2: `patrimonio`
```json
{
  "id": "uuid",
  "politico_id": "uuid",
  
  // Empresas
  "empresas": [
    {
      "rut_empresa": "76.123.456-7",
      "razon_social": "Inversiones Pérez Ltda.",
      "tipo_sociedad": "Limitada",
      "rol": "Socio",
      "porcentaje_participacion": 35.5,
      "fecha_inicio_participacion": "2015-03-20",
      "estado": "Activa"
    }
  ],
  
  // Acciones en bolsas
  "acciones": [
    {
      "emisor": "Cencosud S.A.",
      "numero_acciones": 5000,
      "porcentaje_total": 0.05
    }
  ],
  
  // Bienes raíces
  "bienes_raices": [
    {
      "tipo": "Casa",
      "comuna": "Las Condes",
      "avaluo_fiscal": 50000000,
      "fecha_adquisicion": "2018-01-15"
    }
  ],
  
  // Fuentes
  "fuentes": ["Infoprobidad", "SII"],
  "fecha_declaracion": "2022-12-15",
  "periodo_declaracion": "2022"
}
```

### Entidad 3: `eventos` (Alertas Legales y Prensa)
```json
{
  "id": "uuid",
  "politico_id": "uuid",
  
  "tipo_alerta": "corrupción", // corrupcion | colusion | fraude | cohecho | malversacion | trafic | otro
  "subtipo": "malversación de fondos públicos",
  
  "evento": {
    "titulo": "Implicado en Caso SQM",
    "resumen": "Investigado por recibir pagos irregulares...",
    "fecha_inicio": "2015-06-01",
    "fecha_termino": null,
    "estado_actual": "en_revisión" // en_revisión | formalizado | condenado | sobreseido | absuelto
  },
  
  // Evidencia
  "prensa": [
    {
      "titular": "Diputado X recibió pagos de SQM",
      "medio": "CIPER Chile",
      "fecha_publicacion": "2015-06-15",
      "url": "https://ciper.cl/...",
      "cita_relevante": "Según los documentos, el parlamentario recibió...",
      "confianza_ia": "ALTA" // ALTA | MEDIA | BAJA
    }
  ],
  
  "judicial": {
    "rit": "RUC 12345",
    "tribunal": "Tribunal Oral en Lo Penal",
    "fiscal": "Nombre del fiscal",
    "estado_procesal": "condenado",
    "fecha_sentencia": "2019-03-20",
    "pena": "3 años de presidio remitido",
    "url_oficial": "https://pjud.cl/..."
  },
  
  "metadatos": {
    "procesado_por_ia": true,
    "modelo_ia": "gpt-4o",
    "fecha_procesamiento": "2024-01-15",
    "verificado_por_humano": false
  }
}
```

### Entidad 4: `familiares` (Fase 2)
```json
{
  "id": "uuid",
  "politico_id": "uuid",
  
  "parentesco": "cónyuge",
  "familiar": {
    "nombre_completo": "María López Pérez",
    "rut": "11.222.333-4",
    "fecha_nacimiento": "1982-08-20"
  },
  
  // Vinculación empresarial del familiar
  "empresas_asociadas": [
    {
      "rut_empresa": "76.987.654-3",
      "razon_social": "Constructora López",
      "rol_familiar": "Socia gerente",
      "vinculo_politico": "Proveedor del Estado"
    }
  ],
  
  "fuente": "Declaración jurada patrimonio"
}
```

### Entidad 5: `asesores_y_entorno`
```json
{
  "id": "uuid",
  "politico_id": "uuid",
  
  "nombre_completo": "Pedro Gómez",
  "rut": "9.876.543-2",
  "cargo": "Asesor legislativo",
  "institucion": "Cámara de Diputados",
  "periodo": "2022-2026",
  
  // Mismo patrón de patrimonio y eventos
  "patrimonio": {},
  "eventos": []
}
```

---

## Fuentes de Datos

### Fase 1: Identidad y Patrimonio

| Fuente | URL | Datos | Formato |
|--------|-----|-------|---------|
| Cámara de Diputados | opendata.camara.cl | Lista diputados actuales | XML/JSON |
| Senado | senado.cl | Lista senadores | HTML |
| SERVEL | servel.cl | Candidaturas históricas | HTML |
| Infoprobidad | infoprobidad.cl | Declaraciones patrimonio | HTML/PDF |
| Infolobby | infolobby.cl | Reuniones con lobbistas | HTML |

### Fase 1: Prensa e Investigaciones

| Fuente | URL | Tipo | Método |
|--------|-----|------|--------|
| CIPER Chile | ciperchile.cl | Investigación | RSS + Scraping |
| El Mostrador | elmostrador.cl | Noticias | RSS + Scraping |
| BioBioChile | biobiochile.cl | Noticias | RSS |
| La Tercera | latercera.cl | Paywall | Scraping limitado |
| Poder Judicial | pjud.cl | Causas | API/Búsqueda |

### Fase 2: Bases de Datos Empresariales

| Fuente | Datos | URL |
|--------|-------|-----|
| SII | Empresas por RUT | sii.cl |
| Bolsa de Santiago | Acciones | bcentral.cl |
| Registro de Comercio | Sociedades | registrocivil.cl |

---

## Arquitectura del Pipeline de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                    FUENTES DE DATOS                             │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│   Cámara/    │  Infoprobidad │   Medios     │   PJUD/FNE        │
│   Senado     │  Infolobby    │  (RSS/Scrap) │   (APIs)          │
└──────┬───────┴──────┬───────┴──────┬───────┴─────────┬─────────┘
       │              │              │                 │
       ▼              ▼              ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE EXTRACCIÓN                           │
│  • Scraper Diputados  • Parser Infoprobidad  • Lector RSS     │
│  • Parser XML/Web     • Extractores HTML      • API Clients     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE LLM (Prensa)                       │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ Noticia     │───▶│ Prompt IA   │───▶│ JSON Estructurado   │ │
│  │ Raw Text    │    │ (Analista)  │    │ + Cita Textual      │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│                                                                 │
│  Prompt clave: Extrae SOLO lo que dice el texto, con evidencia  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BASE DE DATOS (PostgreSQL)                   │
│                                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐ │
│  │politicos│  │patrimonio│  │eventos  │  │   familiares        │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────────────────────┘ │
│       │            │            │                               │
│       └────────────┴─────┬──────┘                               │
│                          │                                      │
│                    ┌─────▼─────┐                               │
│                    │ Relación  │                               │
│                    │ Many-to-Many│                              │
│                    └───────────┘                                │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API + FRONTEND                               │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ API REST    │───▶│ Búsqueda    │───▶│ Ficha Completa      │ │
│  │ /graphql    │    │ Filtros     │    │ Por Político        │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│                                                                 │
│  Frontend: Perfil = Cargo + Patrimonio + Timeline Legal        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend: Estructura de Páginas

### 1. Home / Dashboard
- **Estadísticas generales**: total políticos, con alertas, casos activos
- **Alertas recientes**: últimos 10 eventos de prensa
- **Búsqueda rápida**: barra prominente

### 2. Página de Políticos
- **Lista/Grid** con filtros:
  - Por institución (Gobierno, Diputados, Senadores)
  - Por partido
  - Por estado legal (limpio, investigado, formalizado, condenado)
  - Por cantidad de alertas
- **Ordenamiento**: nombre, partido, cantidad de casos

### 3. Ficha de Político (El核核)
```
┌──────────────────────────────────────────────────────────────┐
│ [Foto]  Nombre Completo                                       │
│          Cargo: Diputado • Partido • Distrito                 │
│          Estado: ● Verde/Rojo según alertas                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📋 RESUMEN DE RIESGO                                        │
│  ┌────────┬────────┬────────┬────────┐                     │
│  │ Legal  │Patrimonio│Prensa │Familia  │                     │
│  │  🔴3   │  📋 2  │  📰 5  │  👨‍👩‍👧 1  │                     │
│  └────────┴────────┴────────┴────────┘                     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  🏢 PATRIMONIO Y EMPRESAS                                    │
│                                                              │
│  Empresas:                                                   │
│  • Inversiones X Ltda. (Socio 35%) - Activa                  │
│  • Inmobiliaria Y (Acciones 5%) - Activa                     │
│                                                              │
│  [Ver declaración completa en Infoprobidad →]                │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  ⚖️ HISTORIAL LEGAL                                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 2023  Caso Z - INVESTIGADO                            │    │
│  │ "El parlamentario está siendo investigado por..."     │    │
│  │ 📰 CIPER Chile (15/03/2023)                          │    │
│  │ 📁 RUC 12345 - PJUD                                  │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ 2019  Caso Y - CONDENADO (sobreseído 2021)           │    │
│  │ "Condenado por..."                                    │    │
│  │ 📰 El Mostrador (10/06/2019)                         │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  👨‍👩‍👧 FAMILIARES CON VINCULACIÓN EMPRESARIAL              │
│                                                              │
│  Cónyuge: María X                                            │
│  • Socia en Constructora Z (proveedor del Estado)            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  📰 PRENSA RELACIONADA                                       │
│  [Lista de artículos ordenados por fecha]                     │
└──────────────────────────────────────────────────────────────┘
```

### 4. Página de Casos
- Lista de casos de corrupción/colusión
- Políticos envolvidos
- Estado judicial
- Evolución temporal

### 5. Búsqueda Avanzada
- Por nombre
- Por empresa
- Por RUT
- Por tipo de alerta

---

## Stack Tecnológico Recomendado

### Backend
```
• Python 3.11+
• FastAPI (API REST)
• PostgreSQL (Base de datos)
• SQLAlchemy (ORM)
• Alembic (Migraciones)
```

### Scraping y Datos
```
• BeautifulSoup4 (HTML parsing)
• Playwright (JavaScript rendering)
• httpx (Cliente HTTP async)
• feedparser (RSS)
• newspaper3k (Artículos de prensa)
```

### LLM Pipeline
```
• OpenAI API (GPT-4o) o Claude API
• Pydantic (Validación de schemas)
• Temporal/Redis (Cola de trabajos)
```

### Frontend
```
• Next.js 14 (React)
• Tailwind CSS
• shadcn/ui (Componentes)
• TanStack Query (Estado del servidor)
```

### Deployment
```
• Docker + Docker Compose
• Railway / Render / Vercel / Supabase
```

---

## Fases de Desarrollo

### Fase 1: MVP (Semanas 1-4)
- [x] Esqueleto del proyecto
- [x] Extraer lista de diputados y senadores (scrapers implementados, pendiente ejecución/población real)
- [x] Base de datos con modelo Politicos (SQLAlchemy models + migración pg_trgm)
- [x] Frontend básico: lista y ficha — conectado a API real (`GET /api/politicos/`, `GET /api/politicos/{id}`), con fallback a datos de ejemplo si la API no responde
- [ ] 10-20 casos de ejemplo (hardcoded) — quedan solo como fallback dev, falta poblar DB real

### Fase 2: Patrimonio (Semanas 5-8)
- [ ] Integrar Infoprobidad (scraping declaraciones)
- [ ] Modelo Patrimonio + Empresas
- [ ] Mostrar empresas en ficha de político
- [ ] Búsqueda por empresa

### Fase 3: Prensa con IA (Semanas 9-12)
- [ ] Pipeline RSS → scraping → LLM → eventos
- [ ] Integrar CIPER, El Mostrador, BioBioChile
- [ ] Mostrar timeline de alertas en ficha
- [ ] Notificaciones/Alertas

### Fase 4: Judicial (Semanas 13-16)
- [ ] Integrar API/PJUD
- [ ] Vincular causas judiciales a políticos
- [ ] Estado procesal actualizado
- [ ] Búsqueda por RIT/RUC

### Fase 5: Redes Familiares (Semanas 17-20)
- [ ] Extraer familiares de declaraciones
- [ ] Modelo Familiares
- [ ] Cruzar empresas familiares
- [ ] Alertas de conflicto de interés

---

## Métricas de Éxito

- **Cobertura**: 100% de diputados y senadores activos
- **Actualización**: Datos de prensa < 24hrs de antiguedad
- **Precisión LLM**: Citas textuales en 100% de eventos
- **Usabilidad**: Ficha completada en < 3 clicks

---

## Consideraciones Legales

1. **Solo fuentes públicas**: No almacenar datos sensibles no públicos
2. **Derecho de rectificación**: Mecanismo para que políticos soliciten correcciones
3. **Sin juicios de valor**: Solo hechos verificables con citas
4. **Atribución clara**: Siempre linking a fuentes originales

## Changelog de avance (bitácora automática)
- 2026-07-23: fix seguridad — credencial Neon hardcodeada eliminada de config.py/.env.example (rotar password en Neon).
- 2026-07-23: endpoint `GET /api/politicos/buscar/nombre/{nombre}` + índice pg_trgm (búsqueda tolerante a typos/tildes).
- 2026-07-23: frontend conectado a API real (loadPoliticos/loadDetalle), fallback a datos hardcoded si no hay backend/DB.
- 2026-07-23: fix bug — 02_scraper_patrimonio.py tenía SyntaxError (dict mal anidado en lista), no ejecutaba nunca.
- 2026-07-23: fix bug — frontend mapeaba mal empresas de la ficha (venían anidadas en patrimonios[].empresas con razon_social, no nombre_empresa).
- 2026-07-23: limpieza imports/variables muertas (pyflakes) en 8 archivos. Pendiente (bajo riesgo, stubs de scraping incompletos): contenido/data/soup sin usar en 02_scraper_patrimonio.py y scraper_chile.py — requieren acceso real a los sitios para completarse.
- 2026-07-23: RUTs ficticios en populate_database.py confirmados como data de prueba intencional (no se tocan).
- 2026-07-23: fix CORS (allow_origins=* + allow_credentials=True es inválido en navegadores; se quitó credentials ya que no hay auth por cookies).
- 2026-07-23: README actualizado (endpoint buscar/nombre, paso de migración pg_trgm, typo en portugués). requirements.txt: quitadas asyncpg/alembic (no usadas).
- 2026-07-23: [#1] frontend: búsqueda server-side con debounce (300ms) vía `GET /api/politicos/?busqueda=`, en vez de filtrar solo los primeros 100 cargados.
- 2026-07-23: [#4] 12 tests pytest (PoliticosService + smoke test de sintaxis/imports) contra Postgres real de test — detectaron bug real: la búsqueda por nombre no toleraba tildes pese a lo prometido (ILIKE plano). Fix: extensión `unaccent` + query actualizada.
- 2026-07-23: fix arquitectura — `Base.metadata.create_all` se movió de import-time a startup event de FastAPI (importar `app` tocaba la DB real, imposible de testear).
- 2026-07-23: main.py migrado de `@app.on_event("startup")` (deprecado) a `lifespan` handler.
- 2026-07-23: 8 tests de integración HTTP (TestClient) para /health, /api/politicos/, /api/politicos/{id}, /buscar/rut. Suite completa: 20/20 tests OK.
- 2026-07-23: [#3] rate limiting (slowapi) en endpoints públicos sin auth: /api/politicos/ (60/min), /buscar/rut y /buscar/nombre (30/min). Test que confirma 429 al superar el límite. Suite: 21/21 OK.
- 2026-07-23: /health ahora ejecuta SELECT 1 real contra la DB (antes era estático, no detectaba caídas de Neon); 503 si falla.
- 2026-07-23: limpieza deprecations: config.py (SettingsConfigDict), database.py (sqlalchemy.orm.declarative_base), schemas.py (ConfigDict en 4 schemas). Queda pendiente (bajo riesgo, no se toca) datetime.utcnow() en 6 columnas de models.py — cambiarlo altera semántica naive/aware de timestamps ya almacenados.
- 2026-07-23: CI (GitHub Actions) — `.github/workflows/tests.yml`: corre la suite completa (21 tests) contra Postgres real como servicio, en cada push/PR a main. Badge de estado en README.
