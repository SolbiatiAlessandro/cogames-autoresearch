#!/usr/bin/env bash
# =============================================================================
# CoGames Autoresearch Watchdog (v2)
# Called by cron every 30 min. Checks if loop is alive, restarts if not.
# Also cleans up orphan training processes.
# =============================================================================

set -euo pipefail

REPO="$HOME/Projects/cogames-autoresearch"
LOG="$REPO/autoresearch_loop.log"
PID_FILE="$REPO/autoresearch_loop.pid"
OPENCLAW_BIN="/opt/homebrew/bin/openclaw"
WHATSAPP_NUMBER="+12065321138"

cd "$REPO"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WATCHDOG: $*" | tee -a "$LOG"
}

send_whatsapp() {
    "$OPENCLAW_BIN" message send --channel whatsapp --target "$WHATSAPP_NUMBER" --message "$1" 2>>"$LOG" || true
}

is_loop_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    if pgrep -f "autoresearch_loop.sh" > /dev/null 2>&1; then
        return 0
    fi
    return 1
}

start_loop() {
    # Clean up orphan processes first
    pkill -f "multiprocessing.spawn" 2>/dev/null || true
    pkill -f "train\.py" 2>/dev/null || true
    sleep 3

    log "Starting autoresearch loop..."
    nohup bash "$REPO/autoresearch_loop.sh" >> "$LOG" 2>&1 &
    echo $! > "$PID_FILE"
    log "Loop started with PID $(cat "$PID_FILE")"
}

log "=== Watchdog check ==="

if is_loop_running; then
    log "Loop running (PID: $(cat "$PID_FILE" 2>/dev/null || echo '?')). All good."
else
    log "Loop NOT running. Restarting..."
    start_loop
    sleep 5
    if is_loop_running; then
        log "Loop restarted OK."
        send_whatsapp "🔄 CoGames loop restarted by watchdog."
    else
        log "ERROR: Failed to restart!"
        send_whatsapp "🚨 CoGames watchdog: loop failed to restart! Manual intervention needed."
    fi
fi
