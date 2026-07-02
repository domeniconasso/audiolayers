#!/usr/bin/env zsh
set -e

ZSHRC="$HOME/.zshrc"
MARKER="# audiolayers"
ROOT_VAR="AUDIOLAYERS_ROOT"
COMP_FN="_make_audiolayers"

# ── direnv ────────────────────────────────────────────────────────────────────
if ! command -v direnv &>/dev/null; then
  if command -v brew &>/dev/null; then
    brew install direnv
  elif command -v apt-get &>/dev/null; then
    sudo apt-get install -y direnv
  else
    echo "ERRORE: installa direnv manualmente: https://direnv.net"; exit 1
  fi
fi

direnv allow "$(cd "$(dirname "$0")" && pwd)"

# ── direnv hook (idempotente, indipendente dal marker) ────────────────────────
if ! grep -qF 'eval "$(direnv hook zsh)"' "$ZSHRC" 2>/dev/null; then
  printf '\neval "$(direnv hook zsh)"\n' >> "$ZSHRC"
fi

# ── precmd per le completion (marcato, idempotente) ───────────────────────────
if grep -qF "$MARKER" "$ZSHRC" 2>/dev/null; then
  echo "→ completion hook già presente in ~/.zshrc, skip."
else
  cat >> "$ZSHRC" <<ZSHEOF

autoload -Uz compinit && compinit -C

$MARKER
# Carica tutti i file locali dal repo quando ${ROOT_VAR} è settato.
# Il check su _last_root evita di ricaricare ad ogni comando.
_audiolayers_completion_precmd() {
  local cur="\${${ROOT_VAR}:-}"
  [[ "\$cur" == "\${_audiolayers_last_root:-}" ]] && return
  _audiolayers_last_root="\$cur"
  if [[ -n "\$cur" && -d "\$cur/.zsh_completions" ]]; then
    for f in "\$cur"/.zsh_completions/_*(N); do
      source "\$f"
    done
    compdef $COMP_FN make
  fi
}
precmd_functions+=(_audiolayers_completion_precmd)
ZSHEOF
fi

echo "✓ setup completato. Apri un nuovo terminale per attivare le completion."
