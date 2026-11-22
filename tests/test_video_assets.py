"""
Suíte de Testes Automatizados — Artefatos do Vídeo de Demonstração (Roteiro e Metadados)
CARDs 40, 41, 42 / Issues #49, #50, #51, #9 — Sprint M6 (Hackathon ONE G10 - Equipo 22)

Valida que:
1. O roteiro de 3 minutos existe e cumpre os requisitos de tempo estrito (<= 180s).
2. Os 3 fluxos clínicos canônicos (Rotina, Urgência TEP, HitL) estão explicitados no roteiro.
3. Os metadados de publicação (título, descrição, timestamps de capítulos e legendas VTT) estão completos.
4. As menções aos membros da equipe e tecnologias centrais estão presentes.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_roteiro_video_3min_estrutura() -> None:
    """Valida a estrutura do roteiro técnico do vídeo de 3 minutos."""
    roteiro_path = ROOT_DIR / "week6" / "roteiro_video_3min.md"
    assert roteiro_path.exists(), "week6/roteiro_video_3min.md obrigatório não encontrado!"
    
    conteudo = roteiro_path.read_text(encoding="utf-8")
    
    # Valida presença dos 5 blocos temporais dentro do limite de 3 minutos (180 segundos)
    assert "[00:00 - 00:30]" in conteudo
    assert "[00:30 - 01:00]" in conteudo
    assert "[01:00 - 01:45]" in conteudo
    assert "[01:45 - 02:30]" in conteudo
    assert "[02:30 - 03:00]" in conteudo
    
    # Valida menção explícita aos 3 fluxos
    assert "Cenário 1 (Rotina)" in conteudo or "Rotina" in conteudo
    assert "Tromboembolismo Pulmonar Agudo" in conteudo or "TEP" in conteudo
    assert "Human-in-the-Loop" in conteudo or "HitL" in conteudo
    
    # Valida menções de confiabilidade e infraestrutura
    assert "Circuit-Breaker" in conteudo
    assert "Always Free" in conteudo
    assert "Streamlit" in conteudo


def test_video_metadata_estrutura() -> None:
    """Valida metadados de publicação, timestamps para capítulos do YouTube e legendas VTT."""
    meta_path = ROOT_DIR / "week6" / "demo_video_metadata.md"
    assert meta_path.exists(), "week6/demo_video_metadata.md obrigatório não encontrado!"
    
    conteudo = meta_path.read_text(encoding="utf-8")
    
    # Validar presença de Capítulos do YouTube
    assert "0:00" in conteudo
    assert "0:30" in conteudo
    assert "1:00" in conteudo
    assert "1:45" in conteudo
    assert "2:30" in conteudo
    
    # Validar legendas WebVTT
    assert "WEBVTT" in conteudo
    assert "00:00:00.000 -->" in conteudo
    assert "00:02:45.500 --> 00:03:00.000" in conteudo
    
    # Validar squad creditado
    assert "Carlos Magno" in conteudo
    assert "Fernando Szekut" in conteudo
    assert "Helder Costa Amaral" in conteudo
    assert "Alessandro" in conteudo
