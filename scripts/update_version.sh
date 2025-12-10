#!/bin/bash
# Updates version.json with git commit hash, tag, and current datetime

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="${SCRIPT_DIR}/../src/app/version.json"

COMMIT_HASH=$(git rev-parse HEAD)
TAG=$(git describe --tags --always 2>/dev/null || echo "untagged")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$VERSION_FILE" << EOF
{
  "commit_hash": "${COMMIT_HASH}",
  "build_date": "${BUILD_DATE}",
  "tag": "${TAG}"
}
EOF

echo "Updated version.json:"
cat "$VERSION_FILE"
