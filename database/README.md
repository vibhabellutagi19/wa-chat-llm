# Database Setup

This directory contains the PostgreSQL database schema and initialization scripts for the WhatsApp bot.

## Quick Start

### 1. Start PostgreSQL with Docker

```bash
# From project root
docker-compose up -d
```

This will:
- Start PostgreSQL 16 in a Docker container
- Create the database specified in `.env` (default: `whatsapp_bot`)
- Run the initialization script (`init.sql`) automatically
- Persist data in a Docker volume

### 2. Verify Database is Running

```bash
docker-compose ps
```

You should see the `twilio-whatsapp-db` container running.

### 3. Connect to Database

```bash
# Using psql
docker-compose exec postgres psql -U postgres -d whatsapp_bot

# Or connect from host
psql -h localhost -U postgres -d whatsapp_bot
```

### 4. Stop Database

```bash
docker-compose down
```

To remove data as well:
```bash
docker-compose down -v
```

## Database Schema

### Tables

#### `users`
Stores WhatsApp user information.

| Column | Type | Description |
|--------|------|-------------|
| user_id | UUID (PK) | Unique user identifier |
| email | VARCHAR | User email (nullable) |
| phone_number | VARCHAR (UNIQUE) | WhatsApp number (e.g., whatsapp:+1234567890) |
| full_name | VARCHAR | Display name from WhatsApp profile |
| hashed_password | VARCHAR | For future web access (nullable) |
| password_history | JSONB | Password change history (nullable) |
| is_active | BOOLEAN | Account status |
| created_at | TIMESTAMP | Account creation time |
| updated_at | TIMESTAMP | Last update time (auto-updated) |

#### `userchats`
Stores conversation sessions with message history.

| Column | Type | Description |
|--------|------|-------------|
| chat_id | VARCHAR (PK) | Unique chat identifier (16-char hex) |
| customer_id | UUID (FK) | References users.user_id |
| is_active | BOOLEAN | Whether chat is currently active |
| messages | JSONB | Array of message objects |
| created_at | TIMESTAMP | Chat start time |
| updated_at | TIMESTAMP | Last message time (auto-updated) |

### Message Format (JSONB)

Messages are stored as a JSONB array in the `messages` column:

```json
[
  {
    "role": "user",
    "content": "What is Apache Spark?",
    "timestamp": "2025-10-19T11:37:20.759678+00:00"
  },
  {
    "role": "assistant",
    "content": "Apache Spark is a unified analytics engine...",
    "timestamp": "2025-10-19T11:37:22.123456+00:00"
  }
]
```

## Common Database Operations

### View All Users

```sql
SELECT user_id, phone_number, full_name, created_at
FROM users
ORDER BY created_at DESC;
```

### View User's Chats

```sql
SELECT c.chat_id, c.is_active, c.created_at,
       jsonb_array_length(c.messages) as message_count
FROM userchats c
JOIN users u ON c.customer_id = u.user_id
WHERE u.phone_number = 'whatsapp:+1234567890'
ORDER BY c.created_at DESC;
```

### View Messages from a Chat

```sql
SELECT
    chat_id,
    jsonb_array_elements(messages) as message
FROM userchats
WHERE chat_id = '3e1f3ecf80a140f6';
```

### Get User Statistics

```sql
SELECT
    u.phone_number,
    u.full_name,
    COUNT(DISTINCT c.chat_id) as total_chats,
    SUM(jsonb_array_length(c.messages)) as total_messages
FROM users u
LEFT JOIN userchats c ON u.user_id = c.customer_id
GROUP BY u.user_id, u.phone_number, u.full_name;
```

### Clear Old Inactive Chats

```sql
-- Mark chats older than 30 days as inactive
UPDATE userchats
SET is_active = false
WHERE created_at < NOW() - INTERVAL '30 days'
  AND is_active = true;
```

## Backup and Restore

### Backup Database

```bash
# Backup to file
docker-compose exec postgres pg_dump -U postgres whatsapp_bot > backup.sql

# Or with timestamp
docker-compose exec postgres pg_dump -U postgres whatsapp_bot > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U postgres whatsapp_bot < backup.sql
```

## Indexes

The following indexes are automatically created for performance:

- `idx_users_phone_number` - Fast user lookup by phone
- `idx_users_email` - Email lookups
- `idx_users_is_active` - Filter active users
- `idx_userchats_customer_id` - Find all chats for a user
- `idx_userchats_is_active` - Filter active chats
- `idx_userchats_created_at` - Sort chats by date

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs postgres

# Remove old container and try again
docker-compose down -v
docker-compose up -d
```

### Permission errors

Ensure your `.env` file has correct credentials matching `docker-compose.yml`.

### Connection refused

- Verify PostgreSQL is running: `docker-compose ps`
- Check port 5432 is not in use: `lsof -i :5432`
- Verify connection settings in `.env`

### Reset everything

```bash
# Stop and remove everything including data
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Switching Between Memory and Database Storage

Edit `.env` file:

```bash
# Use database (persistent)
STORAGE_BACKEND=database

# Use in-memory (fast, but loses data on restart)
STORAGE_BACKEND=memory
```

Restart your application after changing this setting.
