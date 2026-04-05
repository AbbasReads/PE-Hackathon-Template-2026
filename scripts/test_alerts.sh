#!/usr/bin/env bash
# ============================================================
# Alert Testing Script
# Usage:
#   ./scripts/test_alerts.sh service-down   # Test ServiceDown alert
#   ./scripts/test_alerts.sh errors          # Test HighErrorRate alert
#   ./scripts/test_alerts.sh cpu             # Test HighCPU alert
# ============================================================

set -euo pipefail

APP_URL="${APP_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_alerts() {
    echo ""
    info "Current alert status in Prometheus:"
    curl -s "${PROMETHEUS_URL}/api/v1/alerts" | python3 -m json.tool 2>/dev/null || echo "(Could not fetch alerts)"
    echo ""
    info "Alertmanager alerts:"
    curl -s "${ALERTMANAGER_URL}/api/v2/alerts" | python3 -m json.tool 2>/dev/null || echo "(Could not fetch alerts)"
}

# ---------------------------------------------------------------
# Test 1: Service Down
# ---------------------------------------------------------------
test_service_down() {
    info "=== Testing ServiceDown Alert ==="
    info "Stopping the app container..."
    docker compose stop app-1 app-2 app-3
    info "App stopped. Waiting 3 minutes for alert to fire..."
    info "Check Prometheus alerts at: ${PROMETHEUS_URL}/alerts"
    sleep 180
    check_alerts
    echo ""
    warn "Don't forget to restart the app: docker compose start app-1 app-2 app-3"
}

# ---------------------------------------------------------------
# Test 2: High Error Rate
# ---------------------------------------------------------------
test_errors() {
    info "=== Testing HighErrorRate Alert ==="
    info "Flooding the app with requests that will return 500 errors..."
    info "Sending 500 error requests over ~60 seconds..."

    for i in $(seq 1 200); do
        curl -s -o /dev/null "${APP_URL}/debug/error" &
        # Small delay to spread requests
        if (( i % 20 == 0 )); then
            sleep 1
        fi
    done
    wait

    info "Error flood complete. Alert should fire within ~6 minutes."
    info "Check Prometheus alerts at: ${PROMETHEUS_URL}/alerts"
    info "Waiting 6 minutes..."
    sleep 360
    check_alerts
}

# ---------------------------------------------------------------
# Test 3: High CPU
# ---------------------------------------------------------------
test_cpu() {
    info "=== Testing HighCPU Alert ==="
    info "Triggering CPU spike via /debug/cpu-spike (runs for ~30s per request)..."
    info "Sending 4 concurrent CPU spike requests..."

    for i in $(seq 1 4); do
        curl -s -o /dev/null "${APP_URL}/debug/cpu-spike" &
    done

    info "CPU spike running. Alert should fire within ~3 minutes."
    info "Check Prometheus alerts at: ${PROMETHEUS_URL}/alerts"
    info "Waiting 3 minutes..."
    sleep 180
    check_alerts
}

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
case "${1:-help}" in
    service-down) test_service_down ;;
    errors)       test_errors ;;
    cpu)          test_cpu ;;
    *)
        echo "Usage: $0 {service-down|errors|cpu}"
        echo ""
        echo "  service-down  — Stops the app container to trigger ServiceDown"
        echo "  errors        — Floods the app with 500 errors to trigger HighErrorRate"
        echo "  cpu           — Triggers CPU spike to test HighCPU"
        exit 1
        ;;
esac
