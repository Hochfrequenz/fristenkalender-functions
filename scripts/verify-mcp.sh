#!/usr/bin/env bash
# Verify the /mcp endpoint of a fristenkalender-functions deployment.
#
# Checks (mirroring Hochfrequenz/ahbicht-functions & ahb-tabellen):
#   1. the MCP endpoint answers at /mcp
#   2. when auth is ON: RFC 9728 Protected Resource Metadata is public at
#      /.well-known/oauth-protected-resource/mcp and points at the Auth0 tenant
#   3. when auth is ON: an unauthenticated call is rejected with 401 +
#      WWW-Authenticate carrying the resource_metadata pointer
#
# Usage:
#   scripts/verify-mcp.sh <base-url>
#   EXPECT_AUTH=1 scripts/verify-mcp.sh https://fristenkalender-api.happyfield-64ecc075.westeurope.azurecontainerapps.io
#   scripts/verify-mcp.sh http://localhost:8000   # local dev (auth usually OFF)
#
# Set EXPECT_AUTH=1 to REQUIRE auth to be on (fail unless /mcp answers 401 + RFC 9728).
# Use it for any real deployment -- otherwise a prod that silently shipped with auth
# DISABLED (the worst misconfiguration this script exists to catch) would pass.
#
# Exit code is non-zero if any expected check fails.

set -euo pipefail

BASE="${1:-}"
if [[ -z "$BASE" ]]; then
  echo "usage: [EXPECT_AUTH=1] $0 <base-url>" >&2
  exit 2
fi
BASE="${BASE%/}" # strip trailing slash
EXPECT_AUTH="${EXPECT_AUTH:-}" # non-empty => auth MUST be on (a non-401 /mcp is a failure)

fail=0
note() { printf '  %s\n' "$1"; }
ok() { printf '\033[32mPASS\033[0m %s\n' "$1"; }
bad() {
  printf '\033[31mFAIL\033[0m %s\n' "$1"
  fail=1
}

echo "== verifying MCP at ${BASE}/mcp =="

# 1. unauthenticated POST /mcp
resp="$(curl -si -X POST "${BASE}/mcp" \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' || true)"
# take the LAST HTTP status line so an informational 1xx (e.g. "100 Continue") is not mistaken
# for the real status
status="$(printf '%s' "$resp" | grep -iE '^HTTP/' | tail -1 | sed -E 's|^HTTP/[0-9.]+ ([0-9]{3}).*|\1|' || true)"
www_auth="$(printf '%s' "$resp" | grep -i '^www-authenticate:' || true)"

case "$status" in
  401)
    ok "POST /mcp -> 401 (auth is ON)"
    if printf '%s' "$www_auth" | grep -qi 'resource_metadata='; then
      ok "WWW-Authenticate carries a resource_metadata pointer"
    else
      bad "401 without a WWW-Authenticate: Bearer resource_metadata=... header"
      note "got: ${www_auth:-<none>}"
    fi
    # 2. Protected Resource Metadata must be public and point at the Hochfrequenz tenant
    prm="$(curl -s "${BASE}/.well-known/oauth-protected-resource/mcp" || true)"
    if printf '%s' "$prm" | grep -q '"authorization_servers"'; then
      ok "RFC 9728 metadata is served"
      note "$prm"
      if printf '%s' "$prm" | grep -q 'auth\.hochfrequenz\.de'; then
        ok "authorization server is the Hochfrequenz Auth0 tenant"
      else
        bad "metadata does not point at auth.hochfrequenz.de -- wrong/misconfigured tenant?"
      fi
    else
      bad "no RFC 9728 metadata at /.well-known/oauth-protected-resource/mcp"
      note "got: ${prm:-<none>}"
    fi
    ;;
  200 | 202 | 400)
    # 400 is the expected reply when auth is OFF and the probe carries no MCP session
    # (fastmcp rejects a session-less tools/list). With auth ON the request is rejected
    # with 401 *before* the session check, so a non-401 here always means "live + unauthenticated".
    if [[ -n "$EXPECT_AUTH" ]]; then
      bad "POST /mcp -> ${status} but EXPECT_AUTH=1 requires auth to be ON (expected 401)"
      note "the deployment appears to have auth DISABLED -- check MCP_AUTH0_* on the app"
    else
      ok "POST /mcp -> ${status} (endpoint is live)"
      note "auth appears DISABLED (no MCP_AUTH0_* set) -- fine for local/dev, NOT for prod"
      [[ "$status" == "400" ]] && note "(400 = session-less probe rejected by the MCP transport; endpoint is up)"
    fi
    ;;
  "")
    bad "no HTTP status from ${BASE}/mcp -- is the app deployed and up?"
    ;;
  *)
    bad "POST /mcp -> unexpected status ${status}"
    note "$(printf '%s' "$resp" | head -1)"
    ;;
esac

echo
if [[ "$fail" -eq 0 ]]; then
  echo "all checks passed"
else
  echo "some checks failed" >&2
fi
exit "$fail"
