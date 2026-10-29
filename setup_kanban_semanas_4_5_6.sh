#!/usr/bin/env bash
# ==============================================================================
# MediFlow (Equipo 22) — Provisionamento das Tarefas das Semanas 4, 5 e 6
# Hackathon ONE G10 — Oracle Next Education & Alura
# ==============================================================================
set -euo pipefail

REPO="${1:-No-Country-simulation/G10-BRASIL-equipo-22}"

echo "🏥 Provisionando as 36 Issues das Semanas 4, 5 e 6 no repositório: $REPO"

# ==============================================================================
# SEMANA 4 (02/11 a 06/11/2026) — M4: Banco de Dados OCI, Histórico & CI/CD Actions
# ==============================================================================
echo "📦 Criando Cards da Semana 4 (M4)..."

# Carlos Magno (Tech Lead & SRE)
gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-13] Criar pipeline CI/CD no GitHub Actions (.github/workflows/ci.yml)" \
  --body "Responsável: **Carlos Magno** (Tech Lead & SRE). Automatizar execução de testes pytest e linting a cada Push e PR nas branches de release." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-14] Implementar telemetria de produção e métricas de SLA SRE em JSON" \
  --body "Responsável: **Carlos Magno** (SRE/DevOps). Consolidar histórico de latências, taxa de contingência e monitoramento de SLA < 5000ms." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-15] Executar testes de carga concorrente (10 a 50 requisições simultâneas)" \
  --body "Responsável: **Carlos Magno** (SRE/DevOps). Simular concorrência de requisições de prontuário avaliando o comportamento do LangGraph." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:carlos-sre-ia,priority:differential,sprint:semana-4"

# Fernando Szekut (Frontend & Workflows)
gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-16] Otimizar ingestão multimodal com conversor de PDF e token caching" \
  --body "Responsável: **Fernando Szekut** (Agent Integration). Implementar conversor de PDF escaneado para imagens Base64 com cache de tokens." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:fernando-nexus,priority:differential,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-17] Enriquecer templates de Webhook com link seguro e dados hospitalares" \
  --body "Responsável: **Fernando Szekut** (Workflows). Formatar payloads de webhook com cards detalhados para Discord, Slack e ERPs clínicos." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:fernando-nexus,priority:critical-mvp,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-18] Criar visualizador de status de entrega de Webhooks no Streamlit" \
  --body "Responsável: **Fernando Szekut** (Frontend/UX). Desenvolver aba com histórico de alertas disparados, latência HTTP e reenvio manual." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:fernando-nexus,priority:differential,sprint:semana-4"

# Helder (Banco de Dados & OCI Always Free)
gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-19] Modelar integração com OCI Autonomous Database (ATP Always Free)" \
  --body "Responsável: **Helder** (Banco de Dados). Criar tabelas relacionais com suporte a colunas JSON para histórico médico auditável." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-20] Validar uploads remotos reais com OCI SDK no bucket mediflow" \
  --body "Responsável: **Helder** (OCI Storage). Testar envio de documentos com credenciais reais da tenancy na nuvem da Oracle." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-21] Implementar política de expurgo e retenção de 30 dias na pasta recebidos/" \
  --body "Responsável: **Helder** (Governança OCI). Configurar lifecycle rule ou rotina Python para limpeza preventiva do bucket gratuito." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:helder-data-oci,priority:differential,sprint:semana-4"

# Alessandro (Backend FastAPI & QA)
gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-22] Desenvolver endpoints de busca histórica e filtros por CRM no FastAPI" \
  --body "Responsável: **Alessandro** (Backend FastAPI). Criar rotas /api/v1/documentos/{id} com filtros por CRM, período e nível de prioridade." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-23] Validar conformidade de contratos Pydantic v2 com padrões TISS/TUSS" \
  --body "Responsável: **Alessandro** (Backend & QA). Mapear schemas de autorização de procedimentos hospitalares para convênios." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:alessandro-app,priority:differential,sprint:semana-4"

gh issue create --repo "$REPO" \
  --title "[M4 - Sem 4] [CARD-24] Construir suíte de testes end-to-end automatizada da Semana 4 (pytest)" \
  --body "Responsável: **Alessandro** (QA). Validar endpoints de busca histórica, gravação relacional e assertividade do CI/CD." \
  --milestone "M4: Banco OCI & CI/CD (02/11 a 06/11)" \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-4"

# ==============================================================================
# SEMANA 5 (09/11 a 13/11/2026) — M5: Interface Streamlit, Visualizador & HitL
# ==============================================================================
echo "📦 Criando Cards da Semana 5 (M5)..."

# Carlos Magno (Tech Lead & SRE)
gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-25] Conectar frontend Streamlit à API FastAPI com circuit-breaker SRE" \
  --body "Responsável: **Carlos Magno** (Tech Lead & SRE). Implementar comunicação desacoplada via REST com proteção contra falhas de rede." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-26] Otimizar tempos de inferência reduzindo latência média para < 3s" \
  --body "Responsável: **Carlos Magno** (IA Core). Refinar prompts e heurísticas para aceleração das respostas dos nós de classificação." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:carlos-sre-ia,priority:differential,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-27] Executar chaos testing simulando indisponibilidade de serviços externos" \
  --body "Responsável: **Carlos Magno** (SRE/DevOps). Validar comportamento resiliente do sistema sob estresse e desconexão de APIs de terceiros." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-5"

# Fernando Szekut (Frontend & UX)
gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-28] Implementar visualizador de PDF/imagem lado a lado no Streamlit" \
  --body "Responsável: **Fernando Szekut** (Frontend/UX). Renderizar documento original escaneado em paralelo ao formulário de auditoria médica." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:fernando-nexus,priority:differential,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-29] Aplicar Design System clínico hospitalar completo (badges e alertas sonoros)" \
  --body "Responsável: **Fernando Szekut** (UX/UI). Criar identidade visual acessível com cores de triagem Manchester e notificações de urgência." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:fernando-nexus,priority:differential,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-30] Adicionar filtros dinâmicos na fila de auditoria (especialidade e gravidade)" \
  --body "Responsável: **Fernando Szekut** (Frontend). Permitir que auditores priorizem casos suspeitos de urgência com facilidade." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:fernando-nexus,priority:critical-mvp,sprint:semana-5"

# Helder (Banco de Dados & OCI Always Free)
gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-31] Configurar deploy opcional da aplicação em VM OCI Compute Always Free" \
  --body "Responsável: **Helder** (Infraestrutura OCI). Preparar script de inicialização e systemd service em instância Ubuntu na nuvem Oracle." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:helder-data-oci,priority:differential,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-32] Criar rotina de exportação de dados clínicos em CSV/JSON para prontuários legados" \
  --body "Responsável: **Helder** (Banco de Dados). Viabilizar interoperabilidade exportando laudos e dados de pacientes aprovados." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-33] Emitir auditoria de conformidade orçamentária OCI garantindo R$ 0,00" \
  --body "Responsável: **Helder** (FinOps OCI). Gerar relatório comprovando cumprimento estrito dos limites gratuitos vitalícios." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-5"

# Alessandro (Backend FastAPI & QA)
gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-34] Implementar módulo de auditoria reversa (reabertura de laudos aprovados)" \
  --body "Responsável: **Alessandro** (Backend FastAPI). Permitir que supervisores médicos solicitem revisão de laudos previamente liberados." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:alessandro-app,priority:differential,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-35] Executar testes de aceitação de usuário (UAT) com 20 laudos e receitas" \
  --body "Responsável: **Alessandro** (QA & Testes). Validar a usabilidade e assertividade da triagem médica em casos clínicos variados." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-5"

gh issue create --repo "$REPO" \
  --title "[M5 - Sem 5] [CARD-36] Atualizar documentação interativa Swagger e contratos de integração REST" \
  --body "Responsável: **Alessandro** (Backend). Finalizar especificações OpenAPI e schemas para avaliação da banca examinadora." \
  --milestone "M5: Interface Streamlit & HitL (09/11 a 13/11)" \
  --label "persona:alessandro-app,priority:differential,sprint:semana-5"

# ==============================================================================
# SEMANA 6 (16/11 a 20/11/2026) — M6: Demonstração, Vídeo YouTube & Submissão ONE
# ==============================================================================
echo "📦 Criando Cards da Semana 6 (M6)..."

# Carlos Magno (Tech Lead & SRE)
gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-37] Realizar revisão final de código, cobertura pytest >= 90% e freeze" \
  --body "Responsável: **Carlos Magno** (Tech Lead). Conduzir code review geral, travar dependências e garantir integridade total do repositório." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-38] Gravar demonstração técnica da IA LangGraph e resiliência SRE para o vídeo" \
  --body "Responsável: **Carlos Magno** (Tech Lead & IA). Gravar trecho de apresentação demonstrando nós do grafo e fallback de contingência." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-39] Executar auditoria final de segurança de credenciais e blindagem Git" \
  --body "Responsável: **Carlos Magno** (SRE/DevOps). Checagem com git-secrets/gitleaks garantindo zero vazamento de chaves ou dados sensíveis." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:carlos-sre-ia,priority:critical-mvp,sprint:semana-6"

# Fernando Szekut (Apresentação & UX)
gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-40] Gravar demonstração de UX, visualizador multimodal e alertas em tempo real" \
  --body "Responsável: **Fernando Szekut** (Frontend & Workflows). Gravar trecho do vídeo exibindo o laudo lado a lado e o pop-up de alerta médico." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:fernando-nexus,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-41] Redigir roteiro técnico de 3 minutos do Vídeo Demo para o Hackathon ONE" \
  --body "Responsável: **Fernando Szekut** (UX & Apresentação). Estruturar minutagem dividida entre problema, solução de IA, UX e OCI." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:fernando-nexus,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-42] Co-editar e masterizar o Vídeo Demo em Full HD com legendas acessíveis" \
  --body "Responsável: **Fernando Szekut** (Design & Mídia). Unir as gravações dos 4 integrantes, incluir trilha suave e exportar em 1080p." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:fernando-nexus,priority:differential,sprint:semana-6"

# Helder (Dados & Custos OCI)
gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-43] Gravar demonstração dos buckets OCI Always Free e comprovação de custo zero" \
  --body "Responsável: **Helder** (OCI & Banco de Dados). Gravar trecho do vídeo exibindo o console da Oracle Cloud e os objetos segregados." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-44] Gerar relatório executivo de auditoria de dados e estabilidade da nuvem OCI" \
  --body "Responsável: **Helder** (Dados OCI). Consolidar métricas de volume de objetos e conformidade para envio à banca examinadora." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-45] Realizar snapshot e backup congelado da base de dados para a banca avaliadora" \
  --body "Responsável: **Helder** (Banco de Dados). Garantir que o ambiente de demonstração permaneça idôneo durante o período de avaliação." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:helder-data-oci,priority:critical-mvp,sprint:semana-6"

# Alessandro (Scrum & Submissão)
gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-46] Gravar introdução do vídeo com contexto hospitalar e proposta de valor" \
  --body "Responsável: **Alessandro** (Apresentação & QA). Abrir o vídeo de 3 minutos contextualizando o problema de glosas e triagem manual." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-47] Realizar upload do vídeo no YouTube e configurar metadados e link oficial" \
  --body "Responsável: **Alessandro** (Comunicação). Publicar vídeo no YouTube com descrição detalhada e link do repositório GitHub." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-6"

gh issue create --repo "$REPO" \
  --title "[M6 - Sem 6] [CARD-48] Validar checklist final de submissão do Hackathon ONE e enviar formulário" \
  --body "Responsável: **Alessandro** (Scrum Master). Revisar conformidade dos 4 entregáveis oficiais e submeter no portal da Alura/Oracle." \
  --milestone "M6: Demonstração & Submissão ONE (16/11 a 20/11)" \
  --label "persona:alessandro-app,priority:critical-mvp,sprint:semana-6"

chmod +x "$0"
echo "✅ Todas as 36 Issues das Semanas 4, 5 e 6 foram criadas e vinculadas aos Milestones com sucesso!"

