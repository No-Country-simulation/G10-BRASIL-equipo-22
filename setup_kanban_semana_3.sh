#!/usr/bin/env bash
# ==============================================================================
# MediFlow (Equipo 22) — Automação do Kanban & Issues da Semana 3 (Sprint M3)
# Hackathon ONE G10 — Oracle Next Education & Alura
# Milestone: M3 — Grafo de Decisão Condicional (LangGraph) & Workflows de Notificação
# Período: 26/10/2026 a 30/10/2026 (Segunda a Sexta — Dias Úteis)
# Integrantes:
#   - Carlos Magno: Tech Lead, SRE/DevOps, Arquitetura IA & Python Core
#   - Fernando Szekut: Integração de Agentes, Frontend/UX & Automação de Workflows
#   - Helder: Especialista em Banco de Dados & Persistência OCI Always Free
#   - Alessandro: Desenvolvedor Backend FastAPI, Módulo HitL & QA
# ==============================================================================
set -euo pipefail

REPO="${1:-No-Country-simulation/G10-BRASIL-equipo-22}"

echo "🏥 Configurando as 12 Issues do Kanban da Semana 3 (M3) no repositório: $REPO"

# 1. Criação da Label de Sprint
gh label create "sprint:semana-3" --color "1D76DB" --description "Sprint M3: Grafo LangGraph e Workflows de Notificação" --repo "$REPO" --force || true

# 2. Issues da Persona 1: Carlos Magno (Tech Lead, SRE/DevOps, IA & Python Core)
gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-01] Refatorar mediflow_agent.py com StateGraph formal do LangGraph" \
  --body "Responsável: **Carlos Magno** (Tech Lead & IA). Modelar TypedDict de estado, nós de ingestão, classificação, validação e roteamento condicional com .compile()." \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-02] Implementar telemetria SRE de latência por nó e métricas de SLA" \
  --body "Responsável: **Carlos Magno** (SRE/DevOps). Medir tempo de resposta (ms), registrar provider ativo (NVIDIA NIM vs Fallback) e validar SLA < 5s." \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-03] Executar testes de caos e resiliência de rede para o Fallback SRE" \
  --body "Responsável: **Carlos Magno** (SRE/DevOps). Simular falhas de rede e oscilações da API externa garantindo Zero Downtime na triagem." \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-3"

# 3. Issues da Persona 2: Fernando Szekut (Frontend, Integração de Agentes & Workflows)
gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-04] Desenvolver módulo de Workflows de Notificação (mediflow_notifications.py)" \
  --body "Responsável: **Fernando Szekut** (Workflows & Integração). Implementar despachador de Webhooks HTTP para envio de alertas para canais hospitalares." \
  --label "persona:fernando-nexus,priority:differential,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-05] Conectar Webhook de emergência ao nó de triagem urgente (TEP Agudo / IAM)" \
  --body "Responsável: **Fernando Szekut** (Workflows). Acionar notificação instantânea quando prioridade for Urgente no Cenário 2 com payload seguro." \
  --label "persona:fernando-nexus,priority:critical-mvp,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-06] Criar componente visual de alerta do plantão médico no Streamlit" \
  --body "Responsável: **Fernando Szekut** (Frontend/UX). Exibir pop-up interativo e indicador pulsante na interface quando o agente disparar alerta crítico." \
  --label "persona:fernando-nexus,priority:differential,sprint:semana-3"

# 4. Issues da Persona 3: Helder (Banco de Dados & Persistência OCI Always Free)
gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-07] Implementar persistência auditável transacional de decisões clínicas" \
  --body "Responsável: **Helder** (Banco de Dados & OCI). Gravar histórico estruturado em SQLite local com espelhamento no OCI Object Storage." \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-08] Estruturar segregação dinâmica de pastas por especialidade clínica no bucket OCI" \
  --body "Responsável: **Helder** (Persistência OCI). Organizar prefixos: processados/rotina/{especialidade} e processados/urgentes/{especialidade}." \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-09] Desenvolver script de auditoria de cotas e custos zero (OCI Always Free)" \
  --body "Responsável: **Helder** (Dados OCI). Assegurar cumprimento rígido dos limites de 10 GB e 50k requisições sem custos para a equipe." \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-3"

# 5. Issues da Persona 4: Alessandro (Backend FastAPI, Módulo HitL & QA)
gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-10] Adicionar endpoints de inspeção e telemetria do Grafo no FastAPI" \
  --body "Responsável: **Alessandro** (Backend FastAPI). Criar rotas /api/v1/grafo/estrutura e /api/v1/telemetria expondo o fluxo do LangGraph." \
  --label "persona:alessandro-app,priority:differential,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-11] Construir suíte automatizada de testes pytest para a Semana 3" \
  --body "Responsável: **Alessandro** (QA & Testes). Desenvolver tests/test_semana_3.py validando o grafo, webhooks e os 3 cenários clínicos." \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-3"

gh issue create --repo "$REPO" \
  --title "[M3 - Sem 3] [CARD-12] Organizar e gerenciar as colunas do quadro Kanban no GitHub Projects" \
  --body "Responsável: **Alessandro** (Scrum/QA). Movimentar cards de sprint entre To Do, In Progress, Review e Done acompanhando entregas." \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-3"

chmod +x "$0"
echo "✅ Todas as 12 Issues da Semana 3 (Sprint M3) foram criadas com sucesso no Kanban!"

