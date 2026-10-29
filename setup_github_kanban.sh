#!/usr/bin/env bash
# ==============================================================================
# MediFlow (Equipo 22) — Script de Automação do Kanban & Issues no GitHub CLI
# Hackathon ONE G10 — Oracle Next Education & Alura
# Personas:
#   - Carlos: Arquiteto Carlos Vance (Tech Lead, Líder SRE/DevOps, Arquitetura IA & Python)
#   - Fernando: Fernando Nexus (Engenheiro de Integração de Agentes, Frontend/UX & Workflows)
#   - Helder: Atlas Data (Banco de Dados & Persistência OCI Always Free)
#   - Alessandro: Marcus Builder (Desenvolvedor Backend FastAPI, HitL & QA)
# ==============================================================================
set -euo pipefail

REPO="${1:-No-Country-simulation/G10-BRASIL-equipo-22}"

echo "🏥 Configurando Labels, Milestones e Issues do Kanban MediFlow no repositório: $REPO"

# 1. Criação de Labels Atualizadas com os Perfis dos 4 Integrantes
gh label create "persona:carlos-sre-ia"     --color "0052CC" --description "Carlos: Tech Lead, SRE/DevOps, Arquitetura IA, Python & LangGraph" --repo "$REPO" --force
gh label create "persona:fernando-nexus"    --color "008080" --description "Fernando: Integração de Agentes, Frontend/UX & Automação de Workflows" --repo "$REPO" --force
gh label create "persona:helder-data-oci"   --color "D93F0B" --description "Helder: Especialista Banco de Dados, Persistência OCI Always Free" --repo "$REPO" --force
gh label create "persona:alessandro-app"    --color "5319E7" --description "Alessandro: Desenvolvedor Backend FastAPI, HitL & QA" --repo "$REPO" --force
gh label create "priority:critical-mvp"     --color "FBCA04" --description "Requisito Obrigatório do Checklist de Avaliação ONE G10" --repo "$REPO" --force
gh label create "priority:differential"     --color "0E8A16" --description "Diferencial Competitivo (Painel HitL Streamlit / Webhooks / Deploy OCI)" --repo "$REPO" --force

# 2. Criação de Issues da Semana 2 a Semana 6 com as Responsabilidades dos 4 Integrantes (Dias Úteis: Segunda a Sexta)
gh issue create --repo "$REPO" \
  --title "[M2 - Sem 2 (19-23/10)] Desenhar schemas Pydantic v2 (mediflow_schemas.py) e motor multimodal NVIDIA NIM" \
  --body "Responsável: **Carlos** (Tech Lead, SRE/DevOps, IA). Validar contratos JSON fiéis ao medflow.md e resiliência SRE." \
  --label "persona:carlos-sre-ia,priority:critical-mvp"

gh issue create --repo "$REPO" \
  --title "[M2 - Sem 2 (19-23/10)] Desenvolver pipeline de ingestão multimodal (PDF/Imagem) e protótipo de UX no Streamlit" \
  --body "Responsável: **Fernando Szekut** (Integração de Agentes & Frontend/UX). Apoiar processamento de imagens e layout do painel." \
  --label "persona:fernando-nexus,priority:critical-mvp"

gh issue create --repo "$REPO" \
  --title "[M2 - Sem 2 (19-23/10)] Modelar dados clínicos e persistência no OCI Object Storage Always Free" \
  --body "Responsável: **Helder** (Banco de Dados & Persistência OCI). Provisionar bucket mediflow-documentos-clinicos e oci_storage.py." \
  --label "persona:helder-data-oci,priority:critical-mvp"

gh issue create --repo "$REPO" \
  --title "[M2 - Sem 2 (19-23/10)] Estruturar Kanban no GitHub Projects e catálogo de testes com os 3 cenários clínicos" \
  --body "Responsável: **Alessandro** (Backend & QA). Preparar casos de teste de Rotina, Urgência TEP e Ambiguidade HitL." \
  --label "persona:alessandro-app,priority:critical-mvp"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3 (26-30/10)] Implementar grafo de decisão StateGraph no LangGraph com rotas de emergência e HitL" \
  --body "Responsável: **Carlos** (Tech Lead & IA). Configurar nós de Ingestão, Classificação, Validação e Roteamento condicional." \
  --label "persona:carlos-sre-ia,priority:critical-mvp"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3 (26-30/10)] Integrar Webhooks de alertas em tempo real para o Plantão Médico e notificações de urgência" \
  --body "Responsável: **Fernando Szekut** (Automação de Workflows). Disparo automático de alertas para casos críticos (TEP Agudo / IAM)." \
  --label "persona:fernando-nexus,priority:differential"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4 (02-06/11)] Integrar schema relacional/JSON de histórico clínico e pipeline CI/CD GitHub Actions" \
  --body "Responsáveis: **Helder** (Banco de Dados OCI) e **Carlos** (SRE/DevOps). Automatizar testes pytest a cada PR e validar backup OCI." \
  --label "persona:helder-data-oci,persona:carlos-sre-ia,priority:critical-mvp"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5 (09-13/11)] Desenvolver Painel Streamlit + API FastAPI (app.py) com tela de Auditoria Human-in-the-Loop" \
  --body "Responsáveis: **Alessandro** (Backend FastAPI) e **Fernando Szekut** (Frontend/UX). Criar interface amigável para aprovação de laudos em 1 clique." \
  --label "persona:alessandro-app,persona:fernando-nexus,priority:differential"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6 (16-20/11)] Gravar Vídeo Demo no YouTube demonstrando os 3 cenários e validar checklist final" \
  --body "Responsáveis: **Alessandro & Fernando** (Apresentação, Roteiro e Edição), **Carlos** (Demonstração do Grafo de IA) e **Helder** (Validação OCI)." \
  --label "persona:alessandro-app,persona:fernando-nexus,priority:critical-mvp"

echo "✅ Todas as Labels e Issues do Kanban MediFlow com os 4 integrantes foram configuradas com sucesso!"
