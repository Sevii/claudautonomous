# Kanboard Self-Hosted Setup

Self-hosted [Kanboard](https://kanboard.org) (Kanban project management) using Docker Compose with PostgreSQL.

## Requirements

- Docker and Docker Compose

## Quick Start

```bash
# Copy and edit the environment file
cp .env.example .env
# Change POSTGRES_PASSWORD to something strong

# Start the services
docker compose up -d

# Open in browser
open http://localhost:8080
```

Default login: `admin` / `admin` — change the password immediately after first login.

## Architecture

| Service | Image | Purpose |
|---------|-------|---------|
| `kanboard` | `kanboard/kanboard:v1.2.49` | Kanboard app (Nginx + PHP) |
| `db` | `postgres:16-alpine` | PostgreSQL database |

Data is persisted in three Docker volumes:
- `kanboard_data` — application data (uploads, config)
- `kanboard_plugins` — installed plugins
- `postgres_data` — database files

## Configuration

All settings are in `.env`. Key options:

| Variable | Default | Description |
|----------|---------|-------------|
| `KANBOARD_PORT` | `8080` | Host port for the web UI |
| `POSTGRES_PASSWORD` | `kanboard` | Database password (change this) |
| `PLUGIN_INSTALLER` | `true` | Allow installing plugins from the UI |

Additional Kanboard settings can be added as environment variables or by placing a `config.php` file in the data volume at `/var/www/app/data/config.php`.

## Operations

```bash
# Stop services
docker compose down

# View logs
docker compose logs -f

# Backup database
docker compose exec db pg_dump -U kanboard kanboard > backup.sql

# Restore database
docker compose exec -T db psql -U kanboard kanboard < backup.sql

# Update Kanboard (change image tag in docker-compose.yml, then)
docker compose pull && docker compose up -d
```

## Email

The Docker image does not support `mail`/`sendmail` transports. Configure SMTP via Kanboard's UI under **Settings > Email Settings**, or use environment variables:

```
MAIL_TRANSPORT=smtp
MAIL_SMTP_HOSTNAME=smtp.example.com
MAIL_SMTP_PORT=587
MAIL_SMTP_USERNAME=your-email@example.com
MAIL_SMTP_PASSWORD=your-password
```
