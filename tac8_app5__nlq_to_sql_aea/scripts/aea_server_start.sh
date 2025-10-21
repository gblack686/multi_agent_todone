#!/bin/bash
# Start AEA server in background with nohup

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVER_DIR="adws/adw_triggers"
SERVER_SCRIPT="adw_trigger_aea_server.py"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/aea_server.log"
PID_FILE="$LOG_DIR/aea_server.pid"
PORT=8743

# Set Claude Code path
export CLAUDE_CODE_PATH="/Users/indydevdan/.claude/local/claude"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${RED}AEA server is already running with PID $PID${NC}"
        echo "Stopping existing server..."
        kill $PID
        sleep 2
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID
            sleep 1
        fi
        
        echo -e "${GREEN}✓ Existing server stopped${NC}"
        rm "$PID_FILE"
    else
        echo "Removing stale PID file..."
        rm "$PID_FILE"
    fi
fi

# Check if port is in use (by another process)
if lsof -i:$PORT > /dev/null 2>&1; then
    echo -e "${RED}Port $PORT is in use by another process. Clearing it...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start the server
echo "Starting AEA server on port $PORT..."

cd "$SERVER_DIR" || exit 1

# Function to cleanup on exit
cleanup() {
    echo -e "\n${GREEN}Stopping AEA server...${NC}"
    rm -f "../../$PID_FILE"
    exit 0
}

# Trap EXIT, INT, and TERM signals
trap cleanup EXIT INT TERM

# Save current PID for cleanup
echo $$ > "../../$PID_FILE"

echo -e "${GREEN}✓ AEA server starting...${NC}"
echo "  Port: $PORT"
echo "  Log: $LOG_FILE"
echo "  Stop with: Ctrl+C"
echo ""

# Run server in foreground and tee output to log file
uv run "$SERVER_SCRIPT" 2>&1 | tee "../../$LOG_FILE"