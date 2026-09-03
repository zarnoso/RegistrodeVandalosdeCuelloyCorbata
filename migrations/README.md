# Migraciones de Base de Datos

Esta carpeta contiene scripts SQL para modificar la base de datos Neon PostgreSQL.

## Ejecutar migraciones:

```bash
# Variables de entorno
export DATABASE_URL="postgresql://neondb_owner:TU_CONTRASEÑA@ep-dark-sunset-ah922o3v-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Ejecutar script
psql "$DATABASE_URL" -f migrations/001_pg_trgm_indexes.sql
```

## Migraciones disponibles:

| Archivo | Descripción |
|---|---|
| `001_pg_trgm_indexes.sql` | Índices GIN para búsquedas ILIKE rápidas |

## Nota importante:

Las migraciones se ejecutan directamente contra Neon. No hay sistema de versionamiento automático — cada script es idempotente (usa `IF NOT EXISTS`) y puede ejecutarse múltiples veces sin problemas.
