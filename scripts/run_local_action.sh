#!/usr/bin/env bash
# =============================================================================
# scripts/run_local_action.sh
#
# Run any GitHub Actions workflow locally using 'act'.
# Requires: brew install act + Docker Desktop running
#
# Usage:
#   ./scripts/run_local_action.sh                   # lists available workflows
#   ./scripts/run_local_action.sh v2_render         # run v2_render_on_demand.yml
#   ./scripts/run_local_action.sh lesson_gen 012    # lesson generation for lesson 012
# =============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOWS_DIR="$REPO_ROOT/.github/workflows"

# ─── Color output ─────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "${CYAN}[act]${NC} $*"; }
success() { echo -e "${GREEN}✅${NC} $*"; }
error()   { echo -e "${RED}❌${NC} $*"; exit 1; }

# ─── Pre-flight checks ────────────────────────────────────────────────────────
check_deps() {
  if ! command -v act &>/dev/null; then
    echo -e "${BOLD}act not found.${NC} Installing via Homebrew..."
    brew install act
  fi

  if ! docker info &>/dev/null; then
    error "Docker Desktop is not running. Please start Docker Desktop first."
  fi

  success "act $(act --version) ready. Docker running."
}

# ─── Load environment variables ───────────────────────────────────────────────
load_env() {
  # Try .env file first
  if [ -f "$REPO_ROOT/.env" ]; then
    info "Loading .env file..."
    set -a && source "$REPO_ROOT/.env" && set +a
  fi

  # Build the secrets string for act
  SECRETS_ARGS=""
  [ -n "$GEMINI_API_KEY" ]   && SECRETS_ARGS="$SECRETS_ARGS --secret GEMINI_API_KEY=$GEMINI_API_KEY"
  [ -n "$GITHUB_TOKEN" ]     && SECRETS_ARGS="$SECRETS_ARGS --secret GITHUB_TOKEN=$GITHUB_TOKEN"
  [ -n "$GH_PAT" ]           && SECRETS_ARGS="$SECRETS_ARGS --secret GH_PAT=$GH_PAT"

  if [ -z "$GEMINI_API_KEY" ]; then
    echo ""
    echo -e "${RED}Warning:${NC} GEMINI_API_KEY not set."
    echo "  Set it in .env or export GEMINI_API_KEY=<your-key>"
    echo ""
  fi
}

# ─── List available workflows ─────────────────────────────────────────────────
list_workflows() {
  echo ""
  echo -e "${BOLD}Available workflows:${NC}"
  for f in "$WORKFLOWS_DIR"/*.yml; do
    name=$(basename "$f" .yml)
    trigger=$(grep -m1 "on:" "$f" 2>/dev/null | head -1 || echo "unknown")
    echo -e "  ${CYAN}$name${NC}"
  done
  echo ""
  echo "Usage examples:"
  echo "  ./scripts/run_local_action.sh v2_render_on_demand"
  echo "  ./scripts/run_local_action.sh v2_lesson_generator 012"
  echo ""
}

# ─── Run a workflow ───────────────────────────────────────────────────────────
run_workflow() {
  local workflow_name="$1"
  local lesson_number="${2:-}"

  # Find matching workflow file
  local workflow_file=""
  if [ -f "$WORKFLOWS_DIR/${workflow_name}.yml" ]; then
    workflow_file="$WORKFLOWS_DIR/${workflow_name}.yml"
  else
    # Try partial match
    workflow_file=$(ls "$WORKFLOWS_DIR"/*${workflow_name}*.yml 2>/dev/null | head -1)
  fi

  if [ -z "$workflow_file" ]; then
    error "Workflow not found: $workflow_name. Run without args to list workflows."
  fi

  info "Running: $(basename $workflow_file)"
  info "Repo: $REPO_ROOT"

  # Build inputs JSON for workflow_dispatch
  INPUTS_JSON="{}"
  if [ -n "$lesson_number" ]; then
    INPUTS_JSON="{\"lesson_number\": \"$lesson_number\"}"
    info "Inputs: lesson_number=$lesson_number"
  fi

  # Act configuration
  # -W: workflow file
  # -P: platform mapping (use ubuntu image with enough tools)
  # --rm: remove containers after run
  # -C: working directory
  act workflow_dispatch \
    -W "$workflow_file" \
    -C "$REPO_ROOT" \
    -P ubuntu-latest=catthehacker/ubuntu:act-22.04 \
    --rm \
    --input-string "$INPUTS_JSON" \
    $SECRETS_ARGS \
    "$@"
}

# ─── V3 local pipeline (no Docker needed) ─────────────────────────────────────
run_v3_local() {
  local lesson="${1:-lesson_012}"
  local lang="${2:-en}"

  info "Running V3 local pipeline for $lesson [$lang]..."

  # Find lesson JSON
  lesson_json=$(find "$REPO_ROOT/rag_learning_series" -name "${lesson}.json" | head -1)
  if [ -z "$lesson_json" ]; then
    error "Lesson JSON not found for: $lesson"
  fi

  # Activate venv
  source "$REPO_ROOT/.venv/bin/activate"

  python "$REPO_ROOT/run_pipeline_v3_local.py" \
    --input "$lesson_json" \
    --lang "$lang" \
    "${@:3}"
}

# ─── Main ─────────────────────────────────────────────────────────────────────
check_deps
load_env

case "${1:-}" in
  ""|-h|--help|help)
    list_workflows
    echo "Or run V3 pipeline directly (no Docker needed):"
    echo "  ./scripts/run_local_action.sh v3 lesson_012 en"
    ;;
  v3)
    run_v3_local "${@:2}"
    ;;
  *)
    run_workflow "$@"
    ;;
esac
