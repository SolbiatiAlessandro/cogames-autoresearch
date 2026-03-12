#!/usr/bin/env bash
# =============================================================================
# CoGames Autoresearch — RunPod Setup Script
# Run this ONCE when you start/restart a RunPod pod.
#
# Usage: bash runpod_setup.sh
# =============================================================================

set -euo pipefail

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# =============================================================================
# 1. FIX DNS (the EAI_AGAIN killer)
# =============================================================================
log "Fixing DNS..."

# Write public DNS servers (bypasses RunPod's flaky internal resolver)
cat > /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 1.1.1.1
nameserver 8.8.4.4
EOF
log "DNS set to Google + Cloudflare"

# Disable IPv6 (common cause of EAI_AGAIN in containers)
sysctl -w net.ipv6.conf.all.disable_ipv6=1 2>/dev/null || true
sysctl -w net.ipv6.conf.default.disable_ipv6=1 2>/dev/null || true
log "IPv6 disabled"

# =============================================================================
# 2. INSTALL BASIC TOOLS
# =============================================================================
log "Installing system packages..."
apt-get update -qq
apt-get install -y -qq \
    curl wget git dnsutils net-tools procps htop \
    build-essential sudo >/dev/null 2>&1
log "System packages installed"

# =============================================================================
# 3. VERIFY DNS WORKS
# =============================================================================
log "Testing DNS resolution..."
if nslookup api.anthropic.com >/dev/null 2>&1; then
    log "✅ DNS working — api.anthropic.com resolves"
else
    log "❌ DNS still broken! Try rebooting the pod."
    exit 1
fi

if curl -s --max-time 10 https://api.anthropic.com >/dev/null 2>&1; then
    log "✅ HTTPS to api.anthropic.com works"
else
    log "⚠️  HTTPS test failed (may be normal — API returns error without auth)"
fi

# =============================================================================
# 4. INSTALL UV (Python package manager)
# =============================================================================
if ! command -v uv &>/dev/null; then
    log "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    log "✅ uv installed: $(uv --version)"
else
    log "✅ uv already installed: $(uv --version)"
fi

# =============================================================================
# 5. INSTALL NODE.JS + CLAUDE CODE
# =============================================================================
if ! command -v claude &>/dev/null; then
    log "Installing Claude Code..."
    if ! command -v npm &>/dev/null; then
        log "Installing Node.js first..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null 2>&1
        apt-get install -y -qq nodejs >/dev/null 2>&1
    fi
    npm install -g @anthropic-ai/claude-code 2>&1 | tail -3
    log "✅ Claude Code installed: $(claude --version 2>/dev/null || echo 'check manually')"
else
    log "✅ Claude Code already installed: $(claude --version 2>/dev/null || echo 'installed')"
fi

# =============================================================================
# 6. INSTALL GH CLI
# =============================================================================
if ! command -v gh &>/dev/null; then
    log "Installing GitHub CLI..."
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg 2>/dev/null
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | tee /etc/apt/sources.list.d/github-cli.list >/dev/null
    apt-get update -qq && apt-get install -y -qq gh >/dev/null 2>&1
    log "✅ gh installed: $(gh --version | head -1)"
else
    log "✅ gh already installed: $(gh --version | head -1)"
fi

# =============================================================================
# 7. SET UP PATH
# =============================================================================
export PATH="$HOME/.local/bin:$PATH"
if ! grep -q 'HOME/.local/bin' ~/.bashrc 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# =============================================================================
# 8. CLONE / UPDATE REPO
# =============================================================================
REPO="$HOME/Projects/cogames-autoresearch"

if [[ -d "$REPO" ]]; then
    log "Repo exists, pulling latest..."
    cd "$REPO" && git fetch --all 2>&1 | tail -3
    log "✅ Repo updated"
else
    log "Cloning cogames-autoresearch..."
    mkdir -p "$HOME/Projects"
    cd "$HOME/Projects"
    gh repo clone SolbiatiAlessandro/cogames-autoresearch 2>/dev/null || \
        git clone https://github.com/SolbiatiAlessandro/cogames-autoresearch.git
    log "✅ Repo cloned"
fi

cd "$REPO"

# =============================================================================
# 9. INSTALL PYTHON DEPS
# =============================================================================
log "Installing Python dependencies..."
uv sync 2>&1 | tail -5
log "✅ Python deps installed"

# =============================================================================
# 10. SYSTEM INFO
# =============================================================================
echo ""
FREE_MB=$(awk '/MemAvailable/ {printf "%d", $2/1024}' /proc/meminfo)
TOTAL_MB=$(awk '/MemTotal/ {printf "%d", $2/1024}' /proc/meminfo)
log "Memory: ${FREE_MB}MB free / ${TOTAL_MB}MB total"

if command -v nvidia-smi &>/dev/null; then
    log "GPU:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
fi

# =============================================================================
# DONE
# =============================================================================
echo ""
echo "=========================================="
echo "  ✅ RunPod setup complete!"
echo "=========================================="
echo ""
echo "  DNS:    Google (8.8.8.8) + Cloudflare (1.1.1.1)"
echo "  Repo:   $REPO"
echo "  Memory: ${FREE_MB}MB free / ${TOTAL_MB}MB total"
echo ""
echo "  Next steps:"
echo "    cd $REPO"
echo "    git checkout -b autoresearch/<branch-name>"
echo "    export ANTHROPIC_API_KEY=sk-..."
echo "    claude --dangerously-skip-permissions"
echo "=========================================="
