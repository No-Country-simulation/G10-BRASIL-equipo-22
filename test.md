# 🧪 MediFlow — Guia de Ativação do Ambiente, Execução e Catálogo de Testes

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Iniciativa:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22 (Carlos — Tech Lead & SRE, Fernando Szekut — Frontend/Workflows, Helder — Dados/OCI, Alessandro — Backend/QA)  
**Ambiente de Execução:** WSL (Ubuntu-24.04) · Linux Filesystem (`/home/magno/ONE`) · Python 3.12+  
**Status do Arquivo:** Documento interno de testes e homologação (ignorado no Git via `.gitignore`)  

---

## 1. ⚙️ Sequência de Ativação do Ambiente (WSL Ubuntu 24.04)

> [!IMPORTANT]
> **Boundary SRE:** Todas as instruções devem ser executadas exclusivamente dentro do terminal Bash do Ubuntu 24.04 no caminho `/home/magno/ONE`. Nunca execute scripts ou comandos Python pelo prompt do Windows PowerShell para evitar conflitos de path e ambiente.

### Passo 1.1 — Acessar o Diretório Raiz do Projeto
```bash
cd /home/magno/ONE
pwd
# Deve retornar: /home/magno/ONE
```

### Passo 1.2 — Ativar o Ambiente Virtual (Virtualenv)
```bash
# Caso o .venv já exista:
source .venv/bin/activate

# Ou se desejar recriar do zero:
# python3 -m venv .venv
# source .venv/bin/activate

# Confirmar versão do Python no venv
python --version
# Esperado: Python 3.12.x
```

### Passo 1.3 — Instalar as Dependências do Projeto
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Passo 1.4 — Configuração de Variáveis de Ambiente (`.env`)
Crie ou edite o arquivo local `.env` na raiz do projeto (já protegido no `.gitignore`):

```bash
cat << 'EOF' > .env
# ==============================================================================
# MediFlow — Variáveis de Ambiente & Credenciais
# ==============================================================================

# 1. NVIDIA NIM (build.nvidia.com) — Llama 3.2 11B Vision Instruct
NVIDIA_API_KEY=nvapi-cole_sua_chave_aqui
NVIDIA_MODEL=meta/llama-3.2-11b-vision-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# 2. Google Gemini Multimodal API (Opcional / Provedor Secundário)
GEMINI_API_KEY=

# 3. Oracle Cloud Infrastructure (OCI Always Free)
# Se não configurado, o sistema ativa automaticamente o Fallback Local SRE
OCI_BUCKET_NAME=mediflow-documentos-clinicos
OCI_NAMESPACE=
OCI_CONFIG_FILE=~/.oci/config
OCI_CONFIG_PROFILE=DEFAULT
EOF
```

---

## 2. 🔬 Sequência de Testes e Validação Técnica

### Teste 2.0 — Validação da Conexão com NVIDIA NIM (`meta/llama-3.2-11b-vision-instruct`)
Testa se a chave gerada no `build.nvidia.com` está ativa e respondendo com extração JSON:

```bash
python -c "
import os
import httpx

api_key = os.getenv('NVIDIA_API_KEY', '')
if not api_key or 'cole_sua_chave' in api_key:
    print('ℹ️  NVIDIA_API_KEY não definida no ambiente. O sistema usará o motor heurístico resiliente SRE.')
else:
    url = 'https://integrate.api.nvidia.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {
        'model': 'meta/llama-3.2-11b-vision-instruct',
        'messages': [{'role': 'user', 'content': 'Responda com o JSON: {\"status\": \"ok\", \"modelo\": \"llama-3.2-11b-vision\"}'}],
        'max_tokens': 50
    }
    with httpx.Client(timeout=20.0) as client:
        r = client.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            print('🎉 Conexão com NVIDIA NIM validada com sucesso!')
            print('   Resposta:', r.json()['choices'][0]['message']['content'])
        else:
            print('⚠️ Erro ao conectar com NVIDIA NIM:', r.status_code, r.text)
"
```

### Teste 2.1 — Sanity Check dos Módulos (Imports e Schemas)
Valida a integridade sintática e a compatibilidade dos modelos Pydantic v1/v2:

```bash
python -c "
import mediflow_schemas
import oci_storage
import mediflow_agent
print('✅ Todos os módulos e contratos do MediFlow foram carregados com sucesso!')
"
```

---

### Teste 2.2 — Teste de Persistência e Segregação OCI Object Storage
Valida o serviço `OCIStorageService` e a segregação por prefixos no bucket (com fallback resiliente local SRE):

```bash
python -c "
from oci_storage import OCIStorageService

storage = OCIStorageService()

# 1. Resolver caminhos dos 3 status clínicos
path_raw = storage.resolve_object_path('DOC-TEST-01', False, 'Rotina', is_raw_ingestion=True)
path_urg = storage.resolve_object_path('DOC-TEST-02', False, 'Urgente')
path_hitl = storage.resolve_object_path('DOC-TEST-03', True, 'Revisao_Humana')

assert path_raw == 'recebidos/DOC-TEST-01.json', f'Erro no path raw: {path_raw}'
assert path_urg == 'processados/urgentes/DOC-TEST-02.json', f'Erro no path urgente: {path_urg}'
assert path_hitl == 'auditoria_humana/DOC-TEST-03.json', f'Erro no path HitL: {path_hitl}'

# 2. Salvar payload de teste
info = storage.save_json_object(path_urg, {'documento_id': 'DOC-TEST-02', 'status': 'teste'})
print('✅ OCI Storage Test Concluído com Sucesso!')
print('   Bucket:', info['bucket'])
print('   Objeto:', info['caminho_objeto'])
print('   Status:', info['status_backup'])
"
```

---

### Teste 2.3 — Execução Direta do Grafo do Agente nos 3 Cenários Oficiais
Executa o motor do agente em `mediflow_agent.py` cobrindo o checklist de avaliação do Hackathon:

```bash
python mediflow_agent.py
```

#### ✅ Resultados Esperados por Cenário:

1. **Cenário 1 — Fluxo Padrão de Rotina Aprovado (`DOC-CLIN-2026-1001`)**:
   - `tipo_documento`: *"Receituário Médico"*
   - `nivel_prioridade`: *"Rotina"*
   - `score_confianca_classificacao`: $\ge 0.85$ (ex.: `0.96`)
   - `requer_auditoria_humana`: `false`
   - `destino_principal`: `"Farmacia_Hospitalar"`
   - `caminho_objeto`: `"processados/rotina/DOC-CLIN-2026-1001.json"`

2. **Cenário 2 — Prioridade de Urgência Médica (`DOC-CLIN-2026-8942`)**:
   - `tipo_documento`: *"Laudo de Exame de Imagem"*
   - `nivel_prioridade`: *"Urgente"*
   - `score_confianca_classificacao`: $\ge 0.85$ (ex.: `0.99`)
   - `diagnostico_principal`: *"Tromboembolismo Pulmonar Agudo (TEP)"*
   - `cid_sugerido`: `"I26.9"`
   - `requer_auditoria_humana`: `false`
   - `destino_principal`: `"Fila_Emergencia_Medica"`
   - `notificacao_gerada`: canal `"Alerta_Plantao_Medico"` com alerta clínico de emergência
   - `caminho_objeto`: `"processados/urgentes/DOC-CLIN-2026-8942.json"`

3. **Cenário 3 — Caso Ambíguo / Falta de CRM / HitL (`DOC-CLIN-2026-5503`)**:
   - `tipo_documento`: *"Documento Clínico Ambíguo"*
   - `nivel_prioridade`: *"Revisao_Humana"*
   - `score_confianca_classificacao`: $< 0.85$ (ex.: `0.65`)
   - `requer_auditoria_humana`: `true`
   - `destino_principal`: `"Fila_Revisao_Humana"`
   - `notificacao_gerada`: canal `"Painel_Auditoria_HitL"`
   - `caminho_objeto`: `"auditoria_humana/DOC-CLIN-2026-5503.json"`

---

### Teste 2.4 — Teste da API REST (FastAPI) via Uvicorn e cURL

#### Passo 1: Iniciar o Servidor REST
Em um terminal dedicado dentro do ambiente virtual:
```bash
source .venv/bin/activate
uvicorn app:api --host 0.0.0.0 --port 8000 --reload
```

#### Passo 2: Executar Requisições de Teste (em outro terminal)

##### A. Healthcheck da API
```bash
curl -s http://localhost:8000/health | jq .
```
*Saída esperada:*
```json
{
  "status": "healthy",
  "service": "mediflow-agent",
  "oci_bucket": "mediflow-documentos-clinicos",
  "tier": "OCI Always Free"
}
```

##### B. Disparar Triagem de Urgência (Cenário 2 — TEP Agudo)
```bash
curl -X POST http://localhost:8000/api/v1/triagem \
  -H "Content-Type: application/json" \
  -d '{
    "documento_id": "DOC-CLIN-2026-8942",
    "tipo_arquivo": "PDF",
    "documento_texto": "HOSPITAL SANTA LUCIA - LAUDO DE EXAME RADIOLOGICO. Paciente: Carlos Eduardo Mendes, 52 anos. Solicitante: Dra. Renata Silveira CRM-SP 145892. Exame: Tomografia de Torax com contraste. Indicacao: Suspeita de embolia pulmonar aguda, dispneia subita. Achados: Falha de enchimento em arteria pulmonar principal direita compativel com TEP agudo. CONCLUSÃO: Quadro compativel com Tromboembolismo Pulmonar Agudo. Sugere-se correlacao clinica urgente.",
    "canal_origem": "Pronto_Socorro"
  }' | jq .
```

##### C. Disparar Triagem Ambígua (Cenário 3 — Reteve para Auditoria Humana)
```bash
curl -X POST http://localhost:8000/api/v1/triagem \
  -H "Content-Type: application/json" \
  -d '{
    "documento_id": "DOC-CLIN-2026-5503",
    "tipo_arquivo": "IMAGEM",
    "documento_texto": "RECEITUARIO MANUSCRITO DIGITALIZADO. Paciente: Roberto F. [rasurado / ilegível]. Solicitante: Dr. Plantonista (CRM ausente / ilegível). Prescrição: Metoprolol dosagem borrada ?? mg uso contínuo.",
    "canal_origem": "Triagem_Externa"
  }' | jq .
```

##### D. Consultar Fila de Auditoria Humana (HitL)
```bash
curl -s http://localhost:8000/api/v1/auditoria | jq .
# Deve listar o documento DOC-CLIN-2026-5503 aguardando intervenção
```

##### E. Aprovar Documento pelo Auditor com Correção de CRM
```bash
curl -X POST "http://localhost:8000/api/v1/auditoria/DOC-CLIN-2026-5503/aprovar?crm_corrigido=123456-SP&destino_final=Farmacia_Hospitalar" | jq .
```

---

### Teste 2.5 — Teste da Interface Visual & Painel HitL (Streamlit)

Inicie a aplicação interativa:
```bash
source .venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Abra o navegador no endereço: **`http://localhost:8501`** (ou no IP do WSL correspondente).

#### Roteiro de Demonstração Visual:
1. **Aba 1 (Triagem de Documentos)**:
   - Selecione o preset: `Cenário 2 (Urgência Médica — TEP Agudo — DOC-CLIN-2026-8942)`.
   - Clique em **Executar Triagem Clínica**.
   - Observe o badge vermelho de prioridade **URGENTE**, o alerta enviado para o plantão e o caminho OCI `/processados/urgentes/`.
2. **Aba 2 (Painel de Auditoria Humana — HitL)**:
   - Processe o `Cenário 3 (Caso Ambíguo / Sem CRM)`.
   - Na Aba 2, veja o card do paciente com campo editável para CRM e botão de **Aprovação do Auditor Humana**.
   - Digite o CRM do médico e aprove o documento com 1 clique.
3. **Aba 3 (Buckets OCI Object Storage Always Free)**:
   - Inspecione a árvore de diretórios local/remota espelhada em `mediflow-documentos-clinicos/`.
   - Verifique os arquivos JSON segregados em `/recebidos`, `/processados/rotina`, `/processados/urgentes` e `/auditoria_humana`.

---

## 3. 🛡️ Suite de Testes Automatizados com Pytest

Para rodar asserções automáticas de ponta a ponta com relatório de cobertura:

```bash
# Executa todos os testes e exibe logs
pytest -v -s
```

*Se preferir rodar um teste headless rápido via script:*
```bash
python -c "
import pytest
from mediflow_agent import MediFlowAgentGraph, SCENARIO_1_ROUTINE, SCENARIO_2_URGENCY_TEP, SCENARIO_3_AMBIGUOUS_HITL

agent = MediFlowAgentGraph()

# Cenário 1
r1 = agent.run(SCENARIO_1_ROUTINE)
assert r1.classificacao.nivel_prioridade.value == 'Rotina'
assert not r1.decisao_roteamento.requer_auditoria_humana
assert 'processados/rotina' in r1.armazenamento_oci.caminho_objeto

# Cenário 2
r2 = agent.run(SCENARIO_2_URGENCY_TEP)
assert r2.classificacao.nivel_prioridade.value == 'Urgente'
assert r2.decisao_roteamento.destino_principal.value == 'Fila_Emergencia_Medica'
assert 'processados/urgentes' in r2.armazenamento_oci.caminho_objeto

# Cenário 3
r3 = agent.run(SCENARIO_3_AMBIGUOUS_HITL)
assert r3.decisao_roteamento.requer_auditoria_humana
assert r3.decisao_roteamento.destino_principal.value == 'Fila_Revisao_Humana'
assert 'auditoria_humana' in r3.armazenamento_oci.caminho_objeto

print('🎉 TODOS OS 3 CENÁRIOS PASSARAM COM 100% DE SUCESSO!')
"
```

---

## 4. 📋 Checklist de Validação Final (Banca ONE G10)

- [ ] Ingestão funcional de documento de texto/PDF.
- [ ] Classificação e extração de dados clínicos estruturados em JSON validado com Pydantic.
- [ ] Grafo de decisão condicional implementado com bifurcações claras.
- [ ] Alerta de emergência clínica disparado para TEP Agudo.
- [ ] Tratamento de caso ambíguo com desvio para auditoria humana (*Human-in-the-Loop*).
- [ ] Persistência com segregação de objetos no OCI Object Storage Always Free.
- [ ] Demonstração prática dos 3 cenários no Streamlit / FastAPI pronta para gravação do vídeo demo no YouTube.

