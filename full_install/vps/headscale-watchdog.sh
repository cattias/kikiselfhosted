# cat /usr/local/bin/headscale-watchdog.sh
#!/bin/bash

# Configuration
SERVICE="headscale"
CHECK_URL="http://127.0.0.1:9090/metrics" # Headscale serves metrics here by default
STUN_PORT=3478
LOG_FILE="/var/log/headscale-watchdog.log"

# Function to log events
log_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# 1. Check if the systemd service is active
if ! systemctl is-active --quiet "$SERVICE"; then
    log_event "CRITICAL: $SERVICE is not running. Attempting restart..."
    systemctl restart "$SERVICE"
    exit 0
fi

# 2. Check if the API/Metrics endpoint is responding
if ! curl -s --fail "$CHECK_URL" > /dev/null; then
    log_event "WARNING: $SERVICE API unresponsive on $CHECK_URL. Restarting..."
    systemctl restart "$SERVICE"
    exit 0
fi

# 3. Check if the STUN port is listening (UDP)
if ! ss -ulpn | grep -q ":$STUN_PORT"; then
    log_event "WARNING: STUN port $STUN_PORT is not listening. Restarting..."
    systemctl restart "$SERVICE"
fi

