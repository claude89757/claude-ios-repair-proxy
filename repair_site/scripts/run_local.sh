#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
. .venv/bin/activate

uvicorn repair_site.status_app.main:app --host 127.0.0.1 --port 9000
