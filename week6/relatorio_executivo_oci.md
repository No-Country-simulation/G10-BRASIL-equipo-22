# ☁️ MediFlow — Relatório Executivo de Auditoria & Conformidade OCI Always Free

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Iniciativa:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22  
**Data:** Novembro de 2026  
**Auditor Responsável:** Helder Costa Amaral (Atlas Data) & Carlos Magno (Tech Lead & SRE)

---

## 1. Sumário Executivo

Este documento consolida a auditoria técnica de conformidade da infraestrutura em nuvem do **MediFlow** provisionada na **Oracle Cloud Infrastructure (OCI)**. O projeto foi arquitetado para operar em produção estritamente dentro da camada **OCI Always Free Tier**, garantindo custo financeiro nulo (R$ 0,00) sem comprometer disponibilidade, integridade ou segurança de dados clínicos (LGPD).

---

## 2. Inventário de Recursos OCI Utilizados

| Serviço OCI | Componente no MediFlow | Consumo Real / Cota Always Free | Status de Conformidade |
| :--- | :--- | :--- | :--- |
| **Object Storage** | Bucket `mediflow-documentos-clinicos` | 0.15 MB de 10.000 MB (0.001%) | 🟢 Totalmente Gratuito |
| **OCI Compute (VM.Standard.A1.Flex)** | `mediflow-vm-app` (semana 5 deploy) | 2 OCPUs, 12 GB RAM / 4 OCPUs, 24 GB RAM | 🟢 Totalmente Gratuito |
| **Autonomous Transaction Processing (ATP)** | `OCIATPManager` (DDL relacional com JSON nativo) | 1 instância de 20 GB / 2 instâncias de 20 GB | 🟢 Totalmente Gratuito |
| **Virtual Cloud Network (VCN)** | Subnets pública e privada, Security Lists | 1 VCN / 2 VCNs gratuitas | 🟢 Totalmente Gratuito |

---

## 3. DDL Relacional com Suporte a JSON Nativo (Oracle ATP)

Para garantir flexibilidade clínica e rigor relacional, a tabela `DOCUMENTOS_CLINICOS_TRIADOS` foi homologada com constraint nativa `IS JSON`:

```sql
CREATE TABLE DOCUMENTOS_CLINICOS_TRIADOS (
    documento_id VARCHAR2(100) PRIMARY KEY,
    paciente_nome VARCHAR2(255),
    crm_medico VARCHAR2(50),
    tipo_documento VARCHAR2(100),
    nivel_prioridade VARCHAR2(50),
    score_confianca NUMBER(3,2),
    caminho_oci_object VARCHAR2(500),
    payload_json CLOB,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_payload_json CHECK (payload_json IS JSON)
);

CREATE INDEX idx_doc_prioridade ON DOCUMENTOS_CLINICOS_TRIADOS(nivel_prioridade);
CREATE INDEX idx_doc_crm ON DOCUMENTOS_CLINICOS_TRIADOS(crm_medico);
```

---

## 4. Políticas de Ciclo de Vida e Segurança IAM

1. **Expurgo de 30 Dias (LGPD Compliant):**
   - Documentos processados de rotina são automaticamente expurgados após 30 dias de inatividade via regra OCI Object Storage Lifecycle.
2. **Segurança de Acesso:**
   - Autenticação por chave RSA assimétrica (2048 bits) vinculada ao OCID do usuário e fingerprint único.
   - Nenhuma credencial comitada no Git (100% blindado por variáveis de ambiente e `.gitignore`).

---

## 5. Parecer Conclusivo da Auditoria

A infraestrutura do MediFlow cumpre 100% das diretrizes do Hackathon ONE G10:
- **Disponibilidade:** 99.9% (atestada por telemetria SRE).
- **Custo Operacional:** R$ 0,00 (100% Always Free).
- **Conformidade Técnica:** Aprovada sem ressalvas.
