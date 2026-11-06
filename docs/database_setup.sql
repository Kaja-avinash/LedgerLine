-- ============================================================================
-- LedgerLine - PostgreSQL development database & role setup
-- ============================================================================
-- Run as a PostgreSQL SUPERUSER (e.g. the 'postgres' account) using psql or
-- pgAdmin's Query Tool. Replace every <..._HERE> placeholder with a real
-- password BEFORE running. Never commit real passwords.
--
-- Roles:
--   ledgerline_migrator : schema owner; runs Alembic migrations (DDL).
--   ledgerline_app      : restricted runtime role (DML only).
--
-- The application role cannot alter schema, disable triggers, or modify
-- historical ledger/audit records because it does not own those objects.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Create roles (idempotent)
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ledgerline_migrator') THEN
        CREATE ROLE ledgerline_migrator WITH
            LOGIN
            PASSWORD '<MIGRATOR_PASSWORD_HERE>'
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            INHERIT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ledgerline_app') THEN
        CREATE ROLE ledgerline_app WITH
            LOGIN
            PASSWORD '<APP_PASSWORD_HERE>'
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            INHERIT;
    END IF;
END
$$;

-- ----------------------------------------------------------------------------
-- 2. Create database owned by the migrator
--    NOTE: CREATE DATABASE cannot run inside a transaction block. In pgAdmin,
--    enable "Auto-commit" (Query Tool -> Auto-commit) or run this statement
--    alone first. In psql it runs standalone.
-- ----------------------------------------------------------------------------
CREATE DATABASE ledgerline_dev
    WITH OWNER = ledgerline_migrator
         ENCODING = 'UTF8'
         LC_COLLATE = 'C'
         LC_CTYPE = 'C'
         TEMPLATE = template0;

-- ----------------------------------------------------------------------------
-- From here on, connect to ledgerline_dev before running:
--   psql:  \c ledgerline_dev
--   pgAdmin: open a new Query Tool on ledgerline_dev
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- 3. Harden defaults: revoke public privileges
-- ----------------------------------------------------------------------------
REVOKE ALL ON DATABASE ledgerline_dev FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ----------------------------------------------------------------------------
-- 4. Schema ownership & grants
-- ----------------------------------------------------------------------------
-- Migrator owns the public schema and can create/alter/drop objects.
ALTER SCHEMA public OWNER TO ledgerline_migrator;
GRANT ALL ON SCHEMA public TO ledgerline_migrator;

-- Migrator must also be able to connect to the database (REVOKE FROM PUBLIC
-- above removes the default CONNECT privilege, so grant it explicitly).
GRANT ALL ON DATABASE ledgerline_dev TO ledgerline_migrator;

-- App role: connect + use schema, but no DDL.
GRANT CONNECT ON DATABASE ledgerline_dev TO ledgerline_app;
GRANT USAGE ON SCHEMA public TO ledgerline_app;

-- Default privileges: tables/sequences created by the migrator are usable by app.
ALTER DEFAULT PRIVILEGES FOR ROLE ledgerline_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ledgerline_app;
ALTER DEFAULT PRIVILEGES FOR ROLE ledgerline_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO ledgerline_app;

-- ----------------------------------------------------------------------------
-- 5. Lock down the app role (no escalation)
-- ----------------------------------------------------------------------------
ALTER ROLE ledgerline_app NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- ----------------------------------------------------------------------------
-- 6. Optional: verify
-- ----------------------------------------------------------------------------
-- \du ledgerline_migrator
-- \du ledgerline_app
-- \l ledgerline_dev
