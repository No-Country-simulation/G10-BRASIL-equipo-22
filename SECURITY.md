# 🛡️ Política de Segurança e Governança de Credenciais — MediFlow

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Iniciativa:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22  
**Data da Auditoria:** Novembro de 2026  
**Status da Auditoria:** 🟢 Aprovado — 0 Credenciais Vazadas (Zero-Leak Enforced)

---

## 1. Princípios de Segurança & Arquitetura Zero Trust

O **MediFlow** adota a filosofia de segurança em profundidade (*Defense in Depth*) e arquitetura Zero Trust, dado o caráter altamente sensível dos dados clínicos (LGPD - Lei Geral de Proteção de Dados, Lei 13.709/2018):

1. **Blindagem de Credenciais (Zero Hardcoding)**:
   - Nenhuma chave de API, token de autenticação, certificado ou chave privada OCI é comitada no repositório Git.
   - Todas as configurações e segredos são obtidos exclusivamente via variáveis de ambiente (`os.getenv()`) ou cofre de credenciais em tempo de execução.
2. **Camada Always Free da Oracle Cloud (OCI)**:
   - O provisionamento e acesso a recursos OCI (Object Storage, Autonomous Database) utilizam políticas IAM de menor privilégio (*Least Privilege*).
   - O acesso é autenticado via chave privada PEM de 2048-bit com permissões locais estritas (`chmod 600 ~/.oci/oci_api_key.pem`).
3. **Anonimização e Proteção de Dados de Pacientes (PHI / LGPD)**:
   - Os payloads de teste utilizam exclusivamente dados sintéticos gerados para homologação técnica, em estrito cumprimento da LGPD.
   - IDs de documentos são gerados deterministicamente ou por hashing criptográfico SHA-256 (`DOC-CLIN-YYYY-XXXX`).

---

## 2. Varreduras de Segurança e Ferramental Automatizado

O repositório do MediFlow conta com barreiras automáticas contra vazamento de segredos:

| Ferramenta / Camada | Finalidade | Status / Cobertura |
| :--- | :--- | :--- |
| **Gitleaks / Secret Scanning** | Análise estática no pré-push buscando chaves de API, tokens e chaves privadas. | 🟢 0 segredos detectados em 100% dos commits. |
| **`.gitignore` Hermético** | Previne que arquivos `.env`, `*.pem`, `*.key`, `secrets.json`, `.coverage`, bases SQLite locais e caches sejam rastreados. | 🟢 100% aderente. |
| **Suíte de Testes `test_security_audit.py`** | Varredura automatizada contínua por regex buscando padrões de chaves OpenAI (`sk-`), Google Gemini (`AIza...`), NVIDIA NIM (`nvapi-...`) e blocos de chave privada PEM. | 🟢 Aprovado em todos os pipelines. |

---

## 3. Matriz de Variáveis de Ambiente Suportadas

Todas as variáveis devem ser declaradas no arquivo `.env` local (ignorado pelo Git) conforme o modelo abaixo:

```bash
# ==============================================================================
# MediFlow — Variáveis de Ambiente de Produção / Homologação
# ==============================================================================

# LLM Providers (Multimodal Inference)
NVIDIA_API_KEY=nvapi-mock-key-development-only
GEMINI_API_KEY=AIzaSyMockKeyForDevelopmentOnly
OPENAI_API_KEY=sk-mock-key-for-development-only

# Oracle Cloud Infrastructure (OCI) Always Free
OCI_USER_OCID=ocid1.user.oc1..aaaaaaamockuser
OCI_TENANCY_OCID=ocid1.tenancy.oc1..aaaaaaamocktenancy
OCI_FINGERPRINT=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
OCI_KEY_FILE=/home/usuario/.oci/oci_api_key.pem
OCI_REGION=sa-saopaulo-1
OCI_NAMESPACE=mock_oracle_tenancy_ns
OCI_BUCKET_NAME=mediflow-documentos-clinicos

# Circuit-Breaker SRE & Portas de Serviço
MEDIFLOW_API_URL=http://localhost:8000
MEDIFLOW_CB_FAILURE_THRESHOLD=3
MEDIFLOW_CB_COOLDOWN_SECONDS=15
```

---

## 4. Divulgação Responsável de Vulnerabilidades

Caso identifique qualquer potencial fragilidade ou vulnerabilidade de segurança no MediFlow:

1. **Não abra uma Issue pública** no GitHub.
2. Contate diretamente o time de engenharia:
   - **Carlos Magno (Tech Lead & SRE):** `@magnomct` no GitHub.
3. Forneça os detalhes técnicos da vulnerabilidade (passo a passo para reprodução e impacto estimado).
4. O time compromete-se a analisar e emitir patch de correção em até 24 horas úteis.
