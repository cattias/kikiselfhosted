#!/bin/bash

# --- Configuration ---
TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"
REPO="juanfont/headscale"

# 1. Check Service Status
SERVICE_STATUS=$(systemctl is-active headscale)
if [ "$SERVICE_STATUS" != "active" ]; then
    ALERT="⚠️ *CRITICAL: Headscale Brain is DOWN!*%0AStatus: \`$SERVICE_STATUS\`%0A_Attempting to notify the captain..._"
    curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" -d "chat_id=$CHAT_ID" -d "text=$ALERT" -d "parse_mode=Markdown" > /dev/null
fi

# 2. Version Check
# Extract v0.27.1 from your 'headscale version v0.27.1+dirty'
CURRENT_VER=$(headscale version | head -n1 | awk '{print $3}' | cut -d'+' -f1)

# Get latest tag from GitHub (excluding pre-releases/betas for stability)
LATEST_VER=$(curl -s https://api.github.com/repos/$REPO/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ "$CURRENT_VER" != "$LATEST_VER" ] && [ ! -z "$LATEST_VER" ]; then
    UPDATE_MSG="🚀 *New Headscale Release Found!*%0A%0AInstalled: \`$CURRENT_VER\`%0ALatest Stable: \`$LATEST_VER\`%0A%0A[View Changelog](https://github.com/$REPO/releases/latest)"
    curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" -d "chat_id=$CHAT_ID" -d "text=$UPDATE_MSG" -d "parse_mode=Markdown" > /dev/null
fi
