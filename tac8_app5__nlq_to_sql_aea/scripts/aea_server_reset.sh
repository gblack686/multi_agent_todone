#!/bin/bash
# Reset AEA server - stop server, clean database, restart

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="logs"
PID_FILE="$LOG_DIR/aea_server.pid"
DB_PATH="adws/adw_data/aea_agents.db"
DB_BACKUP_DIR="adws/adw_data/backups"
PORT=8743

echo "=== AEA Server Reset ==="

# Step 1: Stop the server if running
echo -n "Stopping AEA server... "
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        sleep 2
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID
        fi
        
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}(not running)${NC}"
    fi
    rm -f "$PID_FILE"
else
    echo -e "${YELLOW}(no PID file)${NC}"
fi

# Also check for any process on the port
if lsof -i:$PORT > /dev/null 2>&1; then
    echo "Killing process on port $PORT..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
fi

# Step 2: Backup database if it exists
if [ -f "$DB_PATH" ]; then
    echo -n "Backing up database... "
    mkdir -p "$DB_BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$DB_BACKUP_DIR/aea_agents_${TIMESTAMP}.db"
    cp "$DB_PATH" "$BACKUP_FILE"
    echo -e "${GREEN}✓${NC} (saved to $BACKUP_FILE)"
    
    # Step 3: Reset database
    echo -n "Resetting database... "
    rm -f "$DB_PATH"
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}No database to reset${NC}"
fi

# Step 4: Clear logs
echo -n "Clearing logs... "
if [ -d "$LOG_DIR" ]; then
    # Archive old log
    if [ -f "$LOG_DIR/aea_server.log" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        mv "$LOG_DIR/aea_server.log" "$LOG_DIR/aea_server_${TIMESTAMP}.log.old"
    fi
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}(no logs)${NC}"
fi

# Step 5: Restart server (optional)
read -p "Do you want to start the server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting fresh AEA server..."
    ./scripts/aea_server_start.sh
else
    echo -e "${YELLOW}Server not started. Run 'scripts/aea_server_start.sh' when ready.${NC}"
fi

echo -e "${GREEN}=== Reset complete ===${NC}"