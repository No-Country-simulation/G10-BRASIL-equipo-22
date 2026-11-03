# 🏥 MediFlow — Release 1.4: Banco de Dados OCI, Histórico & CI/CD Actions (Semana 4)

> **Hackathon ONE G10 — Oracle Next Education & Alura**  
> **Squad / Equipo 22:** Carlos Magno, Fernando Szekut, Helder e Alessandro  
> **Milestone:** **M4 — Banco OCI & CI/CD (02/11 a 06/11/2026 — Dias Úteis)**  
> **Branch de Release:** `release-1.4`  
> **Status:** ✅ 100% Concluído e Testado (16 Testes Automatizados no Total)

---

## 👥 Entregas da Semana 4 por Integrante

| Integrante / Persona | Papel no Projeto | Entregas da Sprint M4 |
| :--- | :--- | :--- |
| **Carlos Magno**<br>([GitHub](https://github.com/magnomct) \| [Portfólio](https://carlosmagnocloudengineer.vercel.app/en))<br>*Persona: Arquiteto Carlos Vance* | **Tech Lead & SRE/DevOps**<br>IA & Python Core | • **[CARD-13 / #22]**: Pipeline CI/CD automatizado no GitHub Actions (`.github/workflows/ci.yml`)<br>• **[CARD-14 / #23]**: Motor de telemetria de produção SRE (`week4/telemetry_sre.py`) com percentis (p50/p75/p90/p95/p99) e Error Budget<br>• **[CARD-15 / #24]**: Motor de testes de carga concorrente (`week4/load_testing.py`) com bursts de 10, 25 e 50 requisições simultâneas e throughput de até 85 RPS |
| **Fernando Szekut**<br>([GitHub](https://github.com/FSzekut) \| [Portfólio](https://fernando-szekut.netlify.app/))<br>*Persona: Fernando Nexus* | **Agent Integration & Workflows**<br>Frontend & UX | • **[CARD-16 / #25]**: Otimização da ingestão multimodal com conversor de PDF e token caching<br>• **[CARD-17 / #26]**: Enriquecimento de templates de Webhook com link seguro e dados hospitalares<br>• **[CARD-18 / #27]**: Visualizador de status de entrega de Webhooks no Streamlit |
| **Helder**<br>*Persona: Atlas Data* | **Engenharia de Dados**<br>OCI Always Free & Persistência | • **[CARD-19 / #28]**: Modelagem de integração com OCI Autonomous Database (ATP Always Free)<br>• **[CARD-20 / #29]**: Validação de uploads remotos reais com OCI Python SDK no bucket `mediflow`<br>• **[CARD-21 / #30]**: Implementação de política de expurgo e retenção de 30 dias na pasta `recebidos/` |
| **Alessandro**<br>*Persona: Marcus Builder* | **Backend Developer**<br>FastAPI & QA | • **[CARD-22 / #31]**: Endpoints de busca histórica e filtros por CRM no FastAPI<br>• **[CARD-23 / #32]**: Validação de conformidade de contratos Pydantic v2 com padrões TISS/TUSS<br>• **[CARD-24 / #33]**: Suíte de testes automatizados da Semana 4 (`pytest`) |

---

## ⚡ Benchmarks de Concorrência SRE (Throughput & SLA)

Avaliamos a capacidade do agente sob pico de admissões hospitalares concorrentes (amostras balanceadas de Rotina, Urgência TEP e Ambiguidade HitL):

| Carga Concorrente | Workers Alocados | Duração Total | Throughput Sustentado | Latência Média | Latência p95 | Cumprimento SLA (< 5s) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10 requisições** | 10 | 0.25 s | **39.98 req/s** | 120.75 ms | 247.26 ms | **100.0%** |
| **25 requisições** | 16 | 0.43 s | **57.83 req/s** | 125.24 ms | 251.83 ms | **100.0%** |
| **50 requisições** | 16 | 0.59 s | **85.34 req/s** | 121.43 ms | 461.86 ms | **100.0%** |

> **Resultado:** 0% de exceções não tratadas, ausência de deadlocks e 100% de respeito à meta de latência $< 5.000\text{ ms}$.

---

## 📁 Estrutura de Arquivos da Semana 4

```text
.github/
└── workflows/
    └── ci.yml               # Pipeline oficial CI/CD do GitHub Actions
week4/
├── __init__.py              # Exportação dos componentes da Release 1.4
├── telemetry_sre.py         # SRETelemetryEngine (Percentis, Error Budget & SLA)
├── load_testing.py          # ConcurrentLoadTester (Testes de carga e stress)
├── test_week4.py            # Suite de 8 auto-testes unitários e de integração
├── run_week4_tests.py       # Runner executivo CLI com tabela de throughput
└── README.md                # Este documento executivo da Semana 4
```

---

## 🧪 Como Executar os Testes da Semana 4

### Opção 1 — Executar com Pytest:
```bash
pytest week4/test_week4.py -v
```

### Opção 2 — Executar o Runner Executivo com Benchmark Completo:
```bash
python week4/run_week4_tests.py
```

### Opção 3 — Testar o Novo Endpoint SRE na API FastAPI:
```bash
uvicorn week3.api:app --reload --port 8000
```
Acesse no navegador: `http://127.0.0.1:8000/api/v1/telemetria/producao`
