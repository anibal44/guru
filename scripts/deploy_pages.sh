#!/bin/bash
# Guru — Cloudflare Pages Deploy Wrapper
# Usage: deploy_pages.sh <directory> <project-name>

set -euo pipefail

DIR="${1:?Usage: deploy_pages.sh <directory> <project-name>}"
PROJECT="${2:?Usage: deploy_pages.sh <directory> <project-name>}"

# Sanitize project name (lowercase, alphanumeric + hyphens only)
PROJECT=$(echo "$PROJECT" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')

echo "================================================"
echo "  GURU — Deploying to Cloudflare Pages"
echo "================================================"
echo "  Directory: $DIR"
echo "  Project:   $PROJECT"
echo ""

# Verify directory exists and has index.html
if [ ! -d "$DIR" ]; then
    echo "ERROR: Directory $DIR does not exist"
    exit 1
fi

if [ ! -f "$DIR/index.html" ]; then
    echo "ERROR: No index.html found in $DIR"
    exit 1
fi

# Create project (idempotent — ignores if exists)
echo "Creating Pages project (if not exists)..."
wrangler pages project create "$PROJECT" --production-branch main 2>/dev/null || true

# Deploy
echo "Deploying..."
DEPLOY_OUTPUT=$(wrangler pages deploy "$DIR" --project-name "$PROJECT" --branch main 2>&1)
echo "$DEPLOY_OUTPUT"

# Extract URL
URL=$(echo "$DEPLOY_OUTPUT" | grep -oE 'https://[a-z0-9-]+\.pages\.dev' | head -1)

if [ -n "$URL" ]; then
    echo ""
    echo "================================================"
    echo "  LIVE: $URL"
    echo "================================================"
else
    echo ""
    echo "Deploy complete. Check: https://${PROJECT}.pages.dev"
fi
