# 📦 MediFlow — Evidência de Layout & Console OCI Object Storage Always Free

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Desafio:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22  
**Responsável Técnico:** Helder Costa Amaral (Atlas Data — OCI Cloud Storage) / Carlos Magno (Tech Lead & SRE)  
**Status do Armazenamento:** 🟢 100% Operacional na Camada Always Free (Custo R$ 0,00)

---

## 1. Estrutura Canônica de Buckets e Pastas no OCI

O **MediFlow** adota segregação dinâmica de documentos clínicos no bucket `mediflow-documentos-clinicos` na região `sa-saopaulo-1` (São Paulo), particionado por gravidade clínica e status de auditoria:

```
oci://mediflow-documentos-clinicos/
├── processados/
│   ├── rotina/
│   │   ├── Cardiologia/
│   │   ├── Pneumologia/
│   │   └── DOC-CLIN-2026-1001.json       # Receita médica de rotina (Aprovada)
│   └── urgentes/
│       ├── Radiologia/
│       └── DOC-CLIN-2026-8942.json       # Laudo de TEP Agudo (Disparo Imediato Plantão)
├── auditoria_humana/
│   └── DOC-CLIN-2026-5503.json           # Caso ambíguo retido para médico auditor
└── raw_ingestion/
    ├── SINT-001.pdf                      # Arquivo original multimodal
    └── SINT-002.jpg                      # Imagem médica pré-processada
```

---

## 2. Validação Remota de Objetos (ETag e Integridade MD5)

Cada objeto enviado para o OCI Object Storage passa pela rotina `validate_remote_upload` implementada em `oci_storage.py`:
- **HeadObject API**: Consulta remota sem download do payload completo.
- **Validação de Tamanho**: Confirmação byte a byte do arquivo gravado.
- **Conferência de ETag**: Hashing criptográfico garantindo ausência de corrupção em trânsito.

---

## 3. Política de Ciclo de Vida (Expurgo Automático de 30 Dias)

Para conformidade com os limites da Camada Always Free (máximo de 10 GB para Object Storage) e diretrizes da LGPD para dados temporários de triagem:
- Regra de Lifecycle OCI: `expurgo-30-dias-processados`.
- Ação: `DELETE` automático de objetos após 30 dias de inatividade na pasta `processados/`.
- Implementação no código: método `obter_regra_lifecycle_expurgo_30_dias()` e rotina de auditoria `executar_politica_expurgo_30_dias()`.

---

## 4. Evidência Financeira de Custo Zero (Always Free)

Conforme atestado pela suíte de testes `week5/auditoria_orcamento_oci.py` e relatório `relatorio_conformidade_orcamentaria_oci.txt`:
- **Capacidade OCI Object Storage Alocada:** 0.12 MB / 10.000 MB (0.001% da cota gratuita).
- **Requisições de Leitura/Escrita:** 1.500 req / 50.000 req gratuitas mensais.
- **Custo Total Apurado:** **R$ 0,00** (Zero cobranças adicionais).
