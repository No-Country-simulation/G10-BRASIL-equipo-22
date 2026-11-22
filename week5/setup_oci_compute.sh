#!/usr/bin/env bash
# =============================================================================
# MediFlow — Script de Provisionamento em VM OCI Compute Always Free (Ubuntu 24.04)
# Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
# CARD-31 (#40) — Persona: Atlas Data (Helder)
# =============================================================================
set -euo pipefail

echo "🏥 [MediFlow] Iniciando configuração de ambiente em VM OCI Compute..."

# Atualização de pacotes do sistema
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y python3.12 python3.12-venv python3-pip git curl ufw

# Liberação de portas no firewall da VM (FastAPI: 8000 / Streamlit: 8501)
echo "🔒 [MediFlow] Configurando regras de firewall local (iptables/ufw)..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8501 -j ACCEPT || true
sudo netfilter-persistent save || true

# Configuração do ambiente virtual Python
echo "🐍 [MediFlow] Configurando ambiente virtual Python 3.12..."
if [ ! -d ".venv" ]; then
    python3.12 -m venv .venv
fi
.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install -r requirements.txt

# Instalação do systemd service
echo "⚙️ [MediFlow] Instalando serviço de inicialização automática systemd..."
sudo cp week5/mediflow.service /etc/systemd/system/mediflow.service
sudo systemctl daemon-reload
sudo systemctl enable mediflow.service
sudo systemctl restart mediflow.service

echo "✅ [MediFlow] Deploy concluído com sucesso!"
echo "   Status do serviço: sudo systemctl status mediflow"
echo "   Logs em tempo real: sudo journalctl -u mediflow -f"
