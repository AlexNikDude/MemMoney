#!/bin/bash

# Supabase Backup Script for MemMoney Bot
# Creates a timestamped backup of the Supabase database

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/supabase_backup_$TIMESTAMP.sql"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | grep -E '(SUPABASE_|POSTGRES_)' | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Check if required variables are set
if [ -z "$SUPABASE_HOST" ] || [ -z "$SUPABASE_PASSWORD" ]; then
    echo "❌ Error: SUPABASE_HOST and SUPABASE_PASSWORD must be set in .env"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "💾 Creating Supabase backup..."
echo "📅 Timestamp: $TIMESTAMP"
echo "🔗 Host: $SUPABASE_HOST"

# Create backup using pg_dump (use port 5432 for direct connection)
PGPASSWORD=$SUPABASE_PASSWORD pg_dump \
  -h "$SUPABASE_HOST" \
  -p 5432 \
  -U "$SUPABASE_USER" \
  -d "$SUPABASE_DB" \
  --no-owner \
  --no-privileges \
  -F p \
  -f "$BACKUP_FILE"

# Compress backup
echo "🗜️  Compressing backup..."
gzip "$BACKUP_FILE"

BACKUP_FILE_GZ="${BACKUP_FILE}.gz"
BACKUP_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)

echo "✅ Backup complete!"
echo "📁 File: $BACKUP_FILE_GZ"
echo "📦 Size: $BACKUP_SIZE"

# Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "supabase_backup_*.sql.gz" -mtime +7 -delete
REMAINING_COUNT=$(find "$BACKUP_DIR" -name "supabase_backup_*.sql.gz" | wc -l | tr -d ' ')
echo "📊 Total backups: $REMAINING_COUNT"