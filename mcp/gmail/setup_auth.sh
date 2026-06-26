#!/usr/bin/env bash
set -euo pipefail

GMAIL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$GMAIL_DIR"

if [[ ! -f "gcp-oauth.keys.json" ]]; then
  cat <<'EOF'
Missing gcp-oauth.keys.json in mcp/gmail/.

Local auth setup:
1. Go to https://console.cloud.google.com/
2. Create or select a project and enable the Gmail API
3. APIs & Services > Credentials > Create Credentials > OAuth client ID
4. Choose "Desktop app" (or "Web application" with redirect URI
   http://localhost:3000/oauth2callback)
5. Download the JSON and save it here as gcp-oauth.keys.json

Then run this script again.
EOF
  exit 1
fi

echo "Starting Gmail OAuth (local auth from $GMAIL_DIR)..."
echo "A browser window should open for Google sign-in."
npx -y @gongrzhe/server-gmail-autoauth-mcp auth

if [[ -f "$HOME/.gmail-mcp/credentials.json" ]]; then
  echo ""
  echo "Authentication complete. Credentials saved to ~/.gmail-mcp/credentials.json"
  echo "Test with: python mcp/gmail/client.py"
else
  echo ""
  echo "Auth command finished, but credentials.json was not found in ~/.gmail-mcp/"
  exit 1
fi
