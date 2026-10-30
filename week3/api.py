"""
MediFlow — API REST Oficial com Inspeção do StateGraph (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Marcus Builder (Alessandro — Desenvolvedor Backend FastAPI & QA)
Colaboração Técnica: Carlos Magno (Tech Lead & SRE), Fernando Szekut (Workflows) & Helder (OCI)
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

# Importação dos schemas oficiais da raiz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mediflow_schemas import DocumentoClinicoInput, ResultadoTriagemOutput

from week3.agent import MediFlowStateGraphAgent
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3

app = FastAPI(
    title="MediFlow Autonomous Clinical Triage API (Release 1.3)",
    description="Agente Autônomo com LangGraph StateGraph, Webhooks de Emergência e OCI Always Free",
    version="1.3.0",
)

# Instâncias dos serviços da Release 1.3
_storage_service = OCIStorageServiceV3()
_notification_dispatcher = NotificationDispatcher()
_agent_instance = MediFlowStateGraphAgent(
    storage_service=_storage_service,
    notification_dispatcher=_notification_dispatcher,
)
_audit_queue: Dict[str, ResultadoTriagemOutput] = {}


@app.get("/", response_class=HTMLResponse)
def index_dashboard() -> str:
    """Interface Gráfica Web Oficial do MediFlow (Release 1.3)."""
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediFlow — Triagem Clínica Autônoma & LangGraph (Release 1.3)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --primary-light: #e0f2fe;
            --success: #16a34a;
            --success-light: #dcfce7;
            --warning: #d97706;
            --warning-light: #fef3c7;
            --danger: #dc2626;
            --danger-light: #fee2e2;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --radius: 12px;
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); padding-bottom: 50px; }
        
        /* Top Navigation Header */
        header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 24px 32px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .header-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        .brand { display: flex; align-items: center; gap: 14px; }
        .brand-icon { font-size: 38px; }
        .brand-title h1 { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
        .brand-title p { font-size: 13px; color: #94a3b8; font-weight: 400; margin-top: 2px; }
        
        .header-links { display: flex; gap: 10px; flex-wrap: wrap; }
        .btn-link {
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .btn-link-primary { background: var(--primary); color: white; }
        .btn-link-primary:hover { background: var(--primary-dark); }
        .btn-link-secondary { background: rgba(255,255,255,0.1); color: #e2e8f0; }
        .btn-link-secondary:hover { background: rgba(255,255,255,0.2); }

        /* Squad Bar */
        .squad-bar {
            background: #ffffff;
            border-bottom: 1px solid var(--border);
            padding: 12px 32px;
        }
        .squad-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            font-size: 13px;
        }
        .squad-members { display: flex; gap: 16px; flex-wrap: wrap; }
        .member-badge {
            background: #f1f5f9;
            padding: 4px 10px;
            border-radius: 6px;
            color: #334155;
            font-size: 12px;
            font-weight: 500;
            border: 1px solid #cbd5e1;
        }
        .member-badge strong { color: #0f172a; }

        /* Main Content Grid */
        .main-container {
            max-width: 1400px;
            margin: 28px auto;
            padding: 0 32px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 28px;
        }
        @media (max-width: 1024px) {
            .main-container { grid-template-columns: 1fr; }
        }

        /* Cards */
        .card {
            background: var(--card-bg);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            border: 1px solid var(--border);
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }
        .card-header h2 { font-size: 18px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 8px; }
        .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-success { background: var(--success-light); color: var(--success); }
        .badge-warning { background: var(--warning-light); color: var(--warning); }
        .badge-danger { background: var(--danger-light); color: var(--danger); }
        .badge-primary { background: var(--primary-light); color: var(--primary); }

        /* Scenarios Quick Buttons */
        .scenarios-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }
        @media (max-width: 640px) {
            .scenarios-grid { grid-template-columns: 1fr; }
        }
        .btn-scenario {
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: #f8fafc;
            color: #1e293b;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .btn-scenario:hover {
            border-color: var(--primary);
            background: var(--primary-light);
            color: var(--primary-dark);
            transform: translateY(-2px);
        }
        .btn-scenario small { font-size: 11px; color: var(--text-muted); font-weight: 400; }

        /* Forms */
        .form-group { display: flex; flex-direction: column; gap: 6px; }
        .form-group label { font-size: 13px; font-weight: 600; color: #334155; }
        .form-control {
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--border);
            font-size: 13px;
            transition: all 0.2s;
            width: 100%;
        }
        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15);
        }
        textarea.form-control { resize: vertical; min-height: 120px; line-height: 1.5; }

        .btn-submit {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            border: none;
            padding: 14px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
        }
        .btn-submit:hover {
            opacity: 0.95;
            transform: translateY(-1px);
        }

        /* Result Panel */
        .result-box {
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            font-size: 13px;
        }
        .result-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .result-row:last-child { border-bottom: none; }
        .result-label { font-weight: 600; color: #475569; }
        .result-value { font-weight: 500; color: #0f172a; text-align: right; }
        pre.json-viewer {
            background: #0f172a;
            color: #38bdf8;
            padding: 14px;
            border-radius: 8px;
            font-size: 12px;
            overflow-x: auto;
            max-height: 320px;
        }

        /* Full Width Section */
        .full-width {
            max-width: 1400px;
            margin: 0 auto 30px auto;
            padding: 0 32px;
        }
        .mermaid-container {
            background: white;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 24px;
            overflow-x: auto;
            text-align: center;
        }

        /* HitL Table */
        .hitl-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .hitl-table th { background: #f1f5f9; padding: 10px 14px; text-align: left; font-weight: 600; color: #334155; }
        .hitl-table td { padding: 12px 14px; border-bottom: 1px solid var(--border); }
        .hitl-action-form { display: flex; gap: 8px; align-items: center; }
        .btn-approve {
            background: var(--success);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-approve:hover { background: #15803d; }
    </style>
</head>
<body>

    <!-- Header -->
    <header>
        <div class="header-container">
            <div class="brand">
                <span class="brand-icon">🏥</span>
                <div class="brand-title">
                    <h1>MediFlow — Release 1.3</h1>
                    <p>Agente Autônomo para Triagem, Extração e Roteamento Clínico · Hackathon ONE G10</p>
                </div>
            </div>
            <div class="header-links">
                <a href="/docs" target="_blank" class="btn-link btn-link-primary">📖 Swagger Docs</a>
                <a href="/redoc" target="_blank" class="btn-link btn-link-secondary">📕 ReDoc</a>
                <a href="/api/v1/grafo/estrutura" target="_blank" class="btn-link btn-link-secondary">🕸️ JSON do Grafo</a>
                <a href="/api/v1/telemetria" target="_blank" class="btn-link btn-link-secondary">📊 Métricas SRE</a>
            </div>
        </div>
    </header>

    <!-- Squad Bar -->
    <div class="squad-bar">
        <div class="squad-container">
            <span style="font-weight: 600; color: #475569;">Squad Equipo 22:</span>
            <div class="squad-members">
                <span class="member-badge"><strong>Carlos Magno</strong> · Tech Lead & SRE/DevOps (IA Core)</span>
                <span class="member-badge"><strong>Fernando Szekut</strong> · Agent Integration & Webhooks</span>
                <span class="member-badge"><strong>Helder</strong> · OCI Always Free & SQLite Audit</span>
                <span class="member-badge"><strong>Alessandro</strong> · Backend FastAPI & QA</span>
            </div>
            <span class="member-badge" style="background: #e0f2fe; border-color: #7dd3fc; color: #0369a1;">
                ⚙️ <strong>Orquestração:</strong> LangGraph StateGraph
            </span>
        </div>
    </div>

    <!-- Main Grid -->
    <div class="main-container">

        <!-- Column 1: Teste Interativo de Triagem -->
        <div class="card">
            <div class="card-header">
                <h2>📥 Ingestão & Triagem Interativa</h2>
                <span class="badge badge-primary">LangGraph Node Pipeline</span>
            </div>

            <p style="font-size: 13px; color: var(--text-muted);">
                Escolha um dos cenários pré-configurados ou digite um texto clínico customizado para processamento em tempo real:
            </p>

            <div class="scenarios-grid">
                <button type="button" class="btn-scenario" onclick="loadScenario(1)">
                    <span>💊 Cenário 1: Rotina</span>
                    <small>Receita Amoxicilina · Farmácia</small>
                </button>
                <button type="button" class="btn-scenario" onclick="loadScenario(2)">
                    <span>🚨 Cenário 2: Urgência</span>
                    <small>TEP Agudo · Webhook Plantão</small>
                </button>
                <button type="button" class="btn-scenario" onclick="loadScenario(3)">
                    <span>⚠️ Cenário 3: HitL</span>
                    <small>Rasura / Sem CRM · Retenção</small>
                </button>
            </div>

            <form id="triageForm" onsubmit="executeTriage(event)">
                <div class="form-group" style="margin-bottom: 12px;">
                    <label for="docId">ID do Documento Clínico:</label>
                    <input type="text" id="docId" class="form-control" value="DOC-CLIN-2026-1001" required>
                </div>

                <div class="form-group" style="margin-bottom: 12px;">
                    <label for="canalOrigem">Canal Hospitalar de Origem:</label>
                    <select id="canalOrigem" class="form-control">
                        <option value="Ambulatorio">Ambulatório Clínico</option>
                        <option value="Pronto_Socorro">Pronto-Socorro / Emergência</option>
                        <option value="Radiologia">Centro de Diagnóstico por Imagem</option>
                        <option value="Internacao">Enfermaria / UTI</option>
                    </select>
                </div>

                <div class="form-group" style="margin-bottom: 16px;">
                    <label for="docText">Texto do Documento Clínico:</label>
                    <textarea id="docText" class="form-control" required></textarea>
                </div>

                <button type="submit" id="btnSubmit" class="btn-submit">
                    ⚡ Executar Triagem no LangGraph StateGraph
                </button>
            </form>
        </div>

        <!-- Column 2: Painel de Decisão em Tempo Real -->
        <div class="card">
            <div class="card-header">
                <h2>📋 Decisão & Extração Clínica</h2>
                <span id="statusBadge" class="badge badge-success">Aguardando Execução</span>
            </div>

            <div id="resultContent" style="display: none;">
                <div class="result-box">
                    <div class="result-row">
                        <span class="result-label">Status da Triagem:</span>
                        <span id="resStatus" class="result-value">-</span>
                    </div>
                    <div class="result-row">
                        <span class="result-label">Tipo de Documento:</span>
                        <span id="resTipo" class="result-value">-</span>
                    </div>
                    <div class="result-row">
                        <span class="result-label">Especialidade / Rota OCI:</span>
                        <span id="resEspecialidade" class="result-value">-</span>
                    </div>
                    <div class="result-row">
                        <span class="result-label">Nível de Prioridade:</span>
                        <span id="resPrioridade" class="result-value">-</span>
                    </div>
                    <div class="result-row">
                        <span class="result-label">Score de Confiança:</span>
                        <span id="resScore" class="result-value">-</span>
                    </div>
                    <div class="result-row">
                        <span class="result-label">Destino do Roteamento:</span>
                        <span id="resDestino" class="result-value" style="font-weight: 700; color: var(--primary);">-</span>
                    </div>
                    <div class="result-row">
                        <span class="result-label">Auditoria Humana (HitL):</span>
                        <span id="resHitl" class="result-value">-</span>
                    </div>
                    <div class="result-row">
                        <span class="result-label">Caminho no OCI Bucket:</span>
                        <span id="resOci" class="result-value" style="font-family: monospace; font-size: 11px;">-</span>
                    </div>
                </div>

                <div class="form-group" style="margin-top: 14px;">
                    <label>Justificativa do Agente:</label>
                    <p id="resJustificativa" style="font-size: 13px; color: #334155; line-height: 1.5; background: #f1f5f9; padding: 12px; border-radius: 8px; border: 1px solid var(--border);"></p>
                </div>

                <div class="form-group" style="margin-top: 14px;">
                    <label>JSON Estruturado de Saída:</label>
                    <pre id="jsonOutput" class="json-viewer"></pre>
                </div>
            </div>

            <div id="emptyResultPlaceholder" style="text-align: center; padding: 60px 20px; color: var(--text-muted);">
                <span style="font-size: 48px; display: block; margin-bottom: 12px;">🩺</span>
                <p style="font-weight: 600; font-size: 15px;">Nenhum documento processado ainda.</p>
                <p style="font-size: 13px;">Selecione um cenário à esquerda e clique em Executar Triagem.</p>
            </div>
        </div>

    </div>

    <!-- Fila de Auditoria Humana (HitL) -->
    <div class="full-width">
        <div class="card">
            <div class="card-header">
                <h2>👩‍⚕️ Fila de Auditoria Humana (Human-in-the-Loop)</h2>
                <button type="button" class="btn-link btn-link-secondary" style="color: #334155; border: 1px solid var(--border);" onclick="refreshAuditQueue()">🔄 Atualizar Fila</button>
            </div>
            <div id="hitlQueueContainer">
                <p style="color: var(--text-muted); font-size: 13px;">Nenhum documento retido na fila no momento.</p>
            </div>
        </div>
    </div>

    <!-- Mermaid StateGraph Architecture -->
    <div class="full-width">
        <div class="card">
            <div class="card-header">
                <h2>🕸️ Topologia do LangGraph StateGraph (Release 1.3)</h2>
                <span class="badge badge-primary">Visualização Dinâmica de Arquitetura</span>
            </div>
            <p style="font-size: 13px; color: var(--text-muted);">
                O fluxo abaixo representa o grafo compilado com nós tipados e arestas condicionais de decisão médica:
            </p>
            <div class="mermaid-container">
                <pre class="mermaid">
flowchart TD
    START([START]) --> Ingestor[IngestorNode / Backup Bruto recebidos/]
    Ingestor --> Classifier[ClassifierExtractorNode / NVIDIA NIM Llama 3.2 11B Vision]
    Classifier --> Validator[ValidatorSRECheckNode / Validação Pydantic v2 & Confiabilidade]
    Validator --> Router{Decisão Condicional}
    
    Router -- "Urgência Médica, qualquer score" --> Emergency[EmergencyRouteNode / Webhook Plantão Médico]
    Router -- "Rotina Ambulatorial & Score >= 0.85" --> Routine[RoutineRouteNode / Farmácia & PEP]
    Router -- "Score < 0.85 ou Rasura/Ambiguidade" --> HitL[HitLRouteNode / Auditoria Humana]
    
    Emergency --> Storage[OCIPersistenceNode / Segregação por Especialidade & SQLite]
    Routine --> Storage
    HitL --> Storage
    Storage --> END_NODE([END])
                </pre>
            </div>
        </div>
    </div>

    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'neutral' });

        const SCENARIOS = {
            1: {
                id: "DOC-CLIN-2026-1001",
                canal: "Ambulatorio",
                text: "CLINICA VIDA PLENA - RECEITUARIO MEDICO\\nPaciente: Mariana Costa Souza, 34 anos.\\nSolicitante: Dr. Henrique Almeida CRM-SP 198432.\\nDiagnóstico: Amigdalite Bacteriana Aguda.\\nPrescrição: Amoxicilina + Clavulanato 875/125mg, 1 comprimido de 12/12h por 7 dias."
            },
            2: {
                id: "DOC-CLIN-2026-8942",
                canal: "Pronto_Socorro",
                text: "HOSPITAL SANTA LUCIA - LAUDO DE TOMOGRAFIA DE TORAX\\nPaciente: Carlos Eduardo Mendes, 52 anos.\\nSolicitante: Dra. Renata Silveira CRM 145892.\\nAchados: Defeito de enchimento oclusivo em artéria pulmonar principal direita compatível com Tromboembolismo Pulmonar Agudo (TEP). Sinais de sobrecarga ventricular direita incipiente.\\nConclusão: Tromboembolismo Pulmonar Agudo (TEP) - Condição de Urgência."
            },
            3: {
                id: "DOC-CLIN-2026-5503",
                canal: "Ambulatorio",
                text: "RECEITA MEDICA - CLINICA CENTRAL\\nPaciente: Roberto F...\\nPrescrição: Metoprolol dosagem borrada ?? mg uso contínuo.\\nAssinatura ilegível. CRM ausente ou rasurado na guia."
            }
        };

        function loadScenario(num) {
            const sc = SCENARIOS[num];
            document.getElementById('docId').value = sc.id;
            document.getElementById('canalOrigem').value = sc.canal;
            document.getElementById('docText').value = sc.text.replace(/\\\\n/g, '\\n');
        }

        // Carrega o cenário 1 por padrão
        loadScenario(1);

        async function executeTriage(e) {
            e.preventDefault();
            const btn = document.getElementById('btnSubmit');
            btn.disabled = true;
            btn.innerText = "⏳ Executando no Grafo LangGraph...";

            const payload = {
                documento_id: document.getElementById('docId').value,
                tipo_arquivo: "TEXTO",
                documento_texto: document.getElementById('docText').value,
                canal_origem: document.getElementById('canalOrigem').value
            };

            try {
                const resp = await fetch('/api/v1/triagem', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();

                document.getElementById('emptyResultPlaceholder').style.display = 'none';
                document.getElementById('resultContent').style.display = 'block';

                const isHitl = data.decisao_roteamento.requer_auditoria_humana;
                const isUrgente = data.classificacao.nivel_prioridade === 'Urgente';

                const statusBadge = document.getElementById('statusBadge');
                if (isHitl) {
                    statusBadge.className = 'badge badge-warning';
                    statusBadge.innerText = 'Retido para Auditoria Humana';
                } else if (isUrgente) {
                    statusBadge.className = 'badge badge-danger';
                    statusBadge.innerText = 'Urgência Crítica Encaminhada';
                } else {
                    statusBadge.className = 'badge badge-success';
                    statusBadge.innerText = 'Processado com Sucesso';
                }

                document.getElementById('resStatus').innerText = data.status;
                document.getElementById('resTipo').innerText = data.classificacao.tipo_documento;
                document.getElementById('resEspecialidade').innerText = data.classificacao.especialidade;
                document.getElementById('resPrioridade').innerText = data.classificacao.nivel_prioridade;
                document.getElementById('resScore').innerText = (data.classificacao.score_confianca_classificacao * 100).toFixed(1) + '%';
                document.getElementById('resDestino').innerText = data.decisao_roteamento.destino_principal;
                document.getElementById('resHitl').innerText = isHitl ? "SIM (Requer Validação)" : "NÃO (Liberação Direta)";
                document.getElementById('resOci').innerText = data.armazenamento_oci.caminho_objeto;
                document.getElementById('resJustificativa').innerText = data.decisao_roteamento.justificativa_roteamento;

                document.getElementById('jsonOutput').innerText = JSON.stringify(data, null, 2);

                refreshAuditQueue();
            } catch (err) {
                alert("Erro ao executar triagem: " + err);
            } finally {
                btn.disabled = false;
                btn.innerText = "⚡ Executar Triagem no LangGraph StateGraph";
            }
        }

        async function refreshAuditQueue() {
            try {
                const resp = await fetch('/api/v1/auditoria');
                const queue = await resp.json();
                const container = document.getElementById('hitlQueueContainer');

                if (!queue || queue.length === 0) {
                    container.innerHTML = '<p style="color: var(--text-muted); font-size: 13px;">Nenhum documento retido na fila no momento.</p>';
                    return;
                }

                let html = '<table class="hitl-table"><thead><tr><th>ID</th><th>Paciente</th><th>Diagnóstico</th><th>Score</th><th>Ação do Auditor</th></tr></thead><tbody>';
                for (const doc of queue) {
                    html += `<tr>
                        <td><strong>${doc.documento_id}</strong></td>
                        <td>${doc.dados_extraidos.paciente?.nome || 'N/A'}</td>
                        <td>${doc.dados_extraidos.diagnostico_principal || 'Aguardando validação'}</td>
                        <td><span class="badge badge-warning">${(doc.classificacao.score_confianca_classificacao * 100).toFixed(0)}%</span></td>
                        <td>
                            <div class="hitl-action-form">
                                <input type="text" id="crm_${doc.documento_id}" class="form-control" style="width: 140px; padding: 4px 8px; font-size: 12px;" placeholder="CRM corrigido" value="198432-SP">
                                <button type="button" class="btn-approve" onclick="approveHitl('${doc.documento_id}')">Aprovar & Liberar</button>
                            </div>
                        </td>
                    </tr>`;
                }
                html += '</tbody></table>';
                container.innerHTML = html;
            } catch (err) {
                console.error("Erro ao carregar fila HitL:", err);
            }
        }

        async function approveHitl(docId) {
            const crm = document.getElementById(`crm_${docId}`).value;
            if (!crm) {
                alert("Por favor, digite o CRM corrigido.");
                return;
            }
            try {
                const resp = await fetch(`/api/v1/auditoria/${docId}/aprovar?crm_corrigido=${encodeURIComponent(crm)}&destino_final=Farmacia_Hospitalar`, {
                    method: 'POST'
                });
                const res = await resp.json();
                alert(`Sucesso! ${res.mensagem}`);
                refreshAuditQueue();
            } catch (err) {
                alert("Erro ao aprovar documento: " + err);
            }
        }

        refreshAuditQueue();
    </script>
</body>
</html>"""


@app.get("/health")
def healthcheck() -> dict:
    """Verifica a integridade dos serviços do MediFlow Release 1.3."""
    compliance = _storage_service.check_always_free_compliance()
    return {
        "status": "healthy",
        "service": "mediflow-agent-v3",
        "version": "1.3.0",
        "orchestration": "LangGraph StateGraph",
        "cloud_storage": {
            "bucket": _storage_service.bucket_name,
            "tier": compliance["tier"],
            "compliance": compliance["compliance_status"],
        },
        "notifications": {
            "webhook_mode": "mock" if _notification_dispatcher.mock_mode else "external",
            "total_alertas_enviados": len(_notification_dispatcher.historico_alertas),
        },
    }


@app.post("/api/v1/triagem", response_model=ResultadoTriagemOutput)
def processar_triagem(payload: DocumentoClinicoInput) -> ResultadoTriagemOutput:
    """
    Executa a triagem clínica através do Grafo de Decisão Condicional do LangGraph.
    """
    resultado = _agent_instance.run(payload)
    if resultado.decisao_roteamento.requer_auditoria_humana:
        _audit_queue[resultado.documento_id] = resultado
    return resultado


@app.get("/api/v1/auditoria", response_model=List[ResultadoTriagemOutput])
def listar_fila_auditoria_humana() -> List[ResultadoTriagemOutput]:
    """Retorna os documentos clínicos retidos na fila de Human-in-the-Loop."""
    return list(_audit_queue.values())


@app.post("/api/v1/auditoria/{documento_id}/aprovar")
def aprovar_documento_hitl(
    documento_id: str,
    crm_corrigido: str = Query(..., description="CRM validado e corrigido pelo auditor (ex.: 154990-SP)"),
    destino_final: str = Query("Farmacia_Hospitalar", description="Destino após aprovação médica"),
) -> dict:
    """Aprova e libera um documento retido com intervenção humana auditável."""
    if documento_id not in _audit_queue:
        raise HTTPException(status_code=404, detail=f"Documento {documento_id} não encontrado na fila HitL.")

    item = _audit_queue.pop(documento_id)
    item.status = "aprovado_pos_auditoria"
    item.dados_extraidos.medico_solicitante.crm = crm_corrigido
    item.decisao_roteamento.requer_auditoria_humana = False

    # Atualiza histórico transacional no SQLite
    _storage_service.update_audit_status(
        documento_id=documento_id,
        novo_status="aprovado_pos_auditoria",
        crm_corrigido=crm_corrigido,
        novo_destino=destino_final,
    )

    return {
        "status": "sucesso",
        "mensagem": f"Documento {documento_id} aprovado com CRM {crm_corrigido} e encaminhado para {destino_final}.",
        "documento_atualizado": item.to_dict(exclude_none=True),
    }


@app.get("/api/v1/grafo/estrutura")
def obter_estrutura_grafo() -> dict:
    """Exprime a topologia do StateGraph compilado e diagrama Mermaid."""
    nodes = [
        "ingestor",
        "classifier_extractor",
        "validator_sre_check",
        "emergency_route",
        "routine_route",
        "hitl_route",
        "oci_persistence",
    ]
    edges = [
        {"from": "START", "to": "ingestor"},
        {"from": "ingestor", "to": "classifier_extractor"},
        {"from": "classifier_extractor", "to": "validator_sre_check"},
        {
            "from": "validator_sre_check",
            "type": "conditional",
            "branches": {
                "emergency_route": "emergency_route",
                "routine_route": "routine_route",
                "hitl_route": "hitl_route",
            },
        },
        {"from": "emergency_route", "to": "oci_persistence"},
        {"from": "routine_route", "to": "oci_persistence"},
        {"from": "hitl_route", "to": "oci_persistence"},
        {"from": "oci_persistence", "to": "END"},
    ]
    return {
        "framework": "LangGraph (StateGraph)",
        "nos": nodes,
        "arestas": edges,
        "mermaid_diagram": _agent_instance.get_graph_mermaid(),
    }


@app.get("/api/v1/telemetria")
def obter_telemetria_sre() -> dict:
    """Retorna métricas de performance SRE, histórico SQLite e SLAs."""
    historico = _storage_service.get_audit_history(limit=50)
    total_triagens = len(historico)
    latencias = [r["latencia_ms"] for r in historico if r.get("latencia_ms")]

    media_latencia = round(sum(latencias) / len(latencias), 2) if latencias else 0.0
    cumprimento_sla = round(sum(1 for l in latencias if l < 5000) / len(latencias) * 100, 2) if latencias else 100.0

    return {
        "total_triagens_registradas": total_triagens,
        "latencia_media_ms": media_latencia,
        "sla_limite_ms": 5000.0,
        "percentual_cumprimento_sla": f"{cumprimento_sla}%",
        "provedor_ia_ativo": "NVIDIA NIM (meta/llama-3.2-11b-vision-instruct)" if _agent_instance.nvidia_api_key else "Heuristic SRE Fallback",
        "historico_recente": historico[:10],
    }


@app.get("/api/v1/notificacoes")
def listar_alertas_notificacoes() -> List[Dict[str, Any]]:
    """Retorna o histórico de Webhooks e notificações de emergência médica disparados."""
    return _notification_dispatcher.get_recent_alerts(limit=20)


@app.get("/api/v1/compliance/oci")
def auditoria_oci_always_free() -> dict:
    """Retorna o status de conformidade da camada Always Free."""
    return _storage_service.check_always_free_compliance()


if __name__ == "__main__":
    import uvicorn

    print("🏥 Iniciando API REST MediFlow Release 1.3 em http://127.0.0.1:8000...")
    print("📖 Swagger Docs em http://127.0.0.1:8000/docs")
    uvicorn.run("week3.api:app", host="0.0.0.0", port=8000, reload=False)

