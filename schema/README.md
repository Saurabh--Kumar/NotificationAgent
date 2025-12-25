# Database Schema

This directory contains SQL scripts for setting up the database schema for the Notification Agent.

## Setup Instructions

1. **Prerequisites**:
   - PostgreSQL 12+
   - `uuid-ossp` extension (included in standard PostgreSQL installation)

2. **Creating the Database**:
   ```bash
   createdb notification_agent
   psql -d notification_agent -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
   ```

3. **Applying the Schema**:
   ```bash
   psql -d notification_agent -f db_schema.sql
   ```

## Schema Management

- The schema is versioned using numbered SQL files (e.g., `001_initial_schema.sql`).
- Each script should be idempotent (can be run multiple times without errors).
- Always include `IF NOT EXISTS` for table/column creation.
- Include comments for complex queries or non-obvious design decisions.

## Adding New Changes

1. Create a new numbered SQL file (e.g., `002_feature_name.sql`).
2. Make your changes using `ALTER TABLE` statements.
3. Update this README if you add new scripts or make significant changes.

## Notes

- All timestamps are stored in UTC.
- Use `TIMESTAMP WITH TIME ZONE` for all timestamp columns.
- Use `UUID` for all primary and foreign keys.
- Include appropriate indexes for frequently queried columns.
