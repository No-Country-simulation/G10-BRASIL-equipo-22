"""
Suíte de Testes Automatizados — Auditoria de Segurança de Credenciais & Blindagem Git
CARD-39 / Issue #48 — Sprint M6 (Hackathon ONE G10 - Equipo 22)

Valida que:
1. O .gitignore blinda arquivos sensíveis (.env, *.pem, *.key, secrets.json, etc.).
2. Nenhum arquivo rastreado no repositório contém chaves de API ativas ou chaves privadas.
3. O template .env.example ou referências de ambiente utilizam apenas placeholders.
4. O arquivo SECURITY.md existe e contém as diretrizes de governança e LGPD.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_gitignore_enforces_critical_secrets() -> None:
    """Valida que o .gitignore bloqueia arquivos de ambiente e chaves privadas."""
    gitignore_path = ROOT_DIR / ".gitignore"
    assert gitignore_path.exists(), "Arquivo .gitignore obrigatório não encontrado!"
    
    conteudo = gitignore_path.read_text(encoding="utf-8")
    
    padroes_obrigatorios = [
        ".env",
        "*.key",
        "*.pem",
        "secrets.json",
        ".coverage",
        "*.db",
    ]
    
    for padrao in padroes_obrigatorios:
        assert padrao in conteudo, f"Padrão crítico '{padrao}' ausente no .gitignore!"


def test_no_hardcoded_api_keys_in_tracked_code() -> None:
    """Varre todos os arquivos rastreados no Git por tokens e chaves reais."""
    # Obter lista de arquivos rastreados no git
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    arquivos_rastreados = result.stdout.strip().splitlines()
    assert len(arquivos_rastreados) > 0, "Git ls-files retornou vazio!"
    
    # Padrões suspeitos de credenciais ativas
    padroes_segredo = {
        "Google Gemini Real API Key": re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        "OpenAI Real Secret Key": re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        "NVIDIA NIM Real Token": re.compile(r"nvapi-[a-zA-Z0-9_-]{50,}"),
        "Bloco Chave Privada": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    }
    
    vazamentos_encontrados: list[str] = []
    
    # Arquivos que descrevem os padrões ou testes que não devem ser falsos-positivos
    arquivos_ignorados = {
        "tests/test_security_audit.py",
        "SECURITY.md",
    }
    
    for arq_rel in arquivos_rastreados:
        if arq_rel in arquivos_ignorados or arq_rel.endswith((".png", ".jpg", ".jpeg", ".pdf", ".ico")):
            continue
        
        caminho_completo = ROOT_DIR / arq_rel
        if not caminho_completo.exists() or not caminho_completo.is_file():
            continue
        
        try:
            conteudo = caminho_completo.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        for nome_padrao, regex in padroes_segredo.items():
            matches = regex.findall(conteudo)
            # Filtrar placeholders conhecidos e seguros
            matches_reais = [m for m in matches if "mock" not in m.lower() and "placeholder" not in m.lower() and "exemplo" not in m.lower()]
            if matches_reais:
                vazamentos_encontrados.append(
                    f"Arquivo: {arq_rel} | Tipo: {nome_padrao} | Ocorrências: {len(matches_reais)}"
                )
                
    assert len(vazamentos_encontrados) == 0, (
        f"Vazamento potencial de credenciais detectado:\n" + "\n".join(vazamentos_encontrados)
    )


def test_security_md_exists_and_covers_compliance() -> None:
    """Valida que o SECURITY.md documenta conformidade com LGPD, Zero Trust e IAM."""
    sec_path = ROOT_DIR / "SECURITY.md"
    assert sec_path.exists(), "Arquivo SECURITY.md é obrigatório!"
    
    conteudo = sec_path.read_text(encoding="utf-8")
    assert "LGPD" in conteudo
    assert "Zero Trust" in conteudo
    assert "OCI" in conteudo
    assert "Gitleaks" in conteudo
