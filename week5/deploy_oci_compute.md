# ☁️ Guia de Deploy — VM OCI Compute Always Free (Ubuntu 24.04)
> **MediFlow** · Hackathon ONE G10 · Equipo 22  
> **Persona:** Atlas Data (Helder — Banco de Dados & Infraestrutura OCI)  
> **Card:** CARD-31 (Issue #40)

---

## 1. Visão Geral da Arquitetura de Deploy

A camada de computação gratuita vitalícia (*Always Free*) da Oracle Cloud Infrastructure oferece instâncias com custo fixo de **R$ 0,00**:
- **Opção 1:** 2 VMs AMD Standard.E2.1.Micro (1/8 OCPU, 1 GB RAM cada)
- **Opção 2 (Recomendada):** Ampere A1 Compute (até 4 OCPUs e 24 GB de RAM)

---

## 2. Passo a Passo de Execução

### Passo 1 — Criar Instância no Console OCI
1. Acesse o console OCI: **Compute** → **Instances** → **Create Instance**.
2. Selecione a imagem **Canonical Ubuntu 24.04**.
3. Escolha a forma **VM.Standard.A1.Flex** (ou `VM.Standard.E2.1.Micro`).
4. Anexe sua chave pública SSH (`id_rsa.pub`).
5. Na VCN (Virtual Cloud Network), adicione uma *Ingress Rule* para as portas TCP `8000` (FastAPI) e `8501` (Streamlit).

### Passo 2 — Conectar e Clonar Repositório
```bash
ssh -i ~/.ssh/sua_chave.key ubuntu@<IP_PUBLICO_OCI>

git clone https://github.com/No-Country-simulation/G10-BRASIL-equipo-22.git
cd G10-BRASIL-equipo-22
```

### Passo 3 — Executar Script de Provisionamento Automático
```bash
chmod +x week5/setup_oci_compute.sh
./week5/setup_oci_compute.sh
```

### Passo 4 — Validar Funcionamento
```bash
# Testar endpoint de healthcheck da API
curl http://localhost:8000/health

# Verificar status do serviço systemd
sudo systemctl status mediflow
```
