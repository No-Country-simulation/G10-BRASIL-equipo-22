#!/usr/bin/env bash
# ==============================================================================
# MediFlow (Equipo 22) — Atribuição Automática de Assignees às Issues
# Mapeia as etiquetas persona:* para os usuários do GitHub correspondentes
# ==============================================================================
set -euo pipefail

REPO="${1:-No-Country-simulation/G10-BRASIL-equipo-22}"

echo "🏥 Atribuindo responsáveis a todas as issues do repositório: $REPO"

# Busca todas as issues e sua label de persona
gh issue list --repo "$REPO" --limit 100 --json number,labels --jq '
  .[] | {
    number: .number,
    persona: ([.labels[].name | select(startswith("persona:"))] | first)
  }
' | while read -r item; do
  number=$(echo "$item" | jq -r '.number')
  persona=$(echo "$item" | jq -r '.persona')

  user=""
  case "$persona" in
    "persona:carlos-sre-ia")
      user="magnomct"
      ;;
    "persona:fernando-nexus")
      user="FSzekut"
      ;;
    "persona:helder-data-oci")
      user="HelderAmaralConsult"
      ;;
    "persona:alessandro-app")
      user="superjonic"
      ;;
  esac

  if [ -n "$user" ]; then
    echo "Atribuindo issue #$number ($persona) para @$user..."
    gh issue edit "$number" --repo "$REPO" --add-assignee "$user" >/dev/null || true
  fi
done

echo "✅ Todos os cards foram atribuídos aos respectivos membros da equipe!"

