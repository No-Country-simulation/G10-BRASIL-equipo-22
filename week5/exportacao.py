"""
MediFlow — Módulo de Interoperabilidade e Exportação para Prontuários Legados (PEP / HIS)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
CARD-32 (#41) — Persona: Atlas Data (Helder — Banco de Dados & OCI)
"""

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def obter_registros_clinicos(
    db_path: str = "mediflow_audit.db",
    crm: Optional[str] = None,
    apenas_aprovados: bool = False,
) -> List[Dict[str, Any]]:
    """Recupera registros do histórico clínico auditável com filtros flexíveis."""
    if not Path(db_path).exists():
        return []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM clinico_audit_historico WHERE 1=1"
        params: List[Any] = []
        if crm:
            query += " AND crm_medico = ?"
            params.append(crm)
        if apenas_aprovados:
            query += " AND requer_auditoria = 0"
        query += " ORDER BY data_criacao DESC"

        rows = conn.execute(query, params).fetchall()
        registros = []
        for r in rows:
            payload = json.loads(r["payload_json"]) if r["payload_json"] else {}
            registros.append({
                "documento_id": r["documento_id"],
                "tipo_documento": r["tipo_documento"],
                "crm_medico": r["crm_medico"],
                "paciente_nome": r["paciente_nome"],
                "prioridade": r["prioridade"],
                "score_confianca": r["score_confianca"],
                "requer_auditoria": bool(r["requer_auditoria"]),
                "data_criacao": r["data_criacao"],
                "diagnostico_principal": payload.get("dados_extraidos", {}).get("diagnostico_principal") or payload.get("diagnostico", "N/A"),
                "cid_sugerido": payload.get("dados_extraidos", {}).get("cid_sugerido") or payload.get("cid10", "N/A"),
                "destino": payload.get("decisao_roteamento", {}).get("destino_principal", "N/A"),
            })
        return registros


def exportar_prontuarios_csv(
    output_path: str,
    db_path: str = "mediflow_audit.db",
    crm: Optional[str] = None,
    apenas_aprovados: bool = False,
) -> int:
    """Exporta histórico clínico em formato CSV padronizado para sistemas legados."""
    registros = obter_registros_clinicos(db_path, crm=crm, apenas_aprovados=apenas_aprovados)
    if not registros:
        # Se não há dados no DB, cria cabeçalho padrão
        campos = [
            "documento_id", "tipo_documento", "crm_medico", "paciente_nome",
            "prioridade", "score_confianca", "requer_auditoria", "data_criacao",
            "diagnostico_principal", "cid_sugerido", "destino"
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
        return 0

    campos = list(registros[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(registros)
    return len(registros)


def exportar_prontuarios_json(
    output_path: str,
    db_path: str = "mediflow_audit.db",
    crm: Optional[str] = None,
    apenas_aprovados: bool = False,
) -> int:
    """Exporta histórico clínico em JSON estruturado com metadados para interoperabilidade."""
    registros = obter_registros_clinicos(db_path, crm=crm, apenas_aprovados=apenas_aprovados)
    export_payload = {
        "sistema_origem": "MediFlow Autonomous Clinical Agent (Release 1.5)",
        "total_registros": len(registros),
        "filtros_aplicados": {"crm": crm, "apenas_aprovados": apenas_aprovados},
        "prontuarios": registros,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, ensure_ascii=False, indent=2)
    return len(registros)


def main():
    parser = argparse.ArgumentParser(description="Exporta prontuários clínicos para CSV ou JSON.")
    parser.add_argument("--formato", choices=["csv", "json"], default="csv", help="Formato de saída")
    parser.add_argument("--saida", required=True, help="Caminho do arquivo gerado")
    parser.add_argument("--crm", help="Filtro opcional por CRM")
    parser.add_argument("--aprovados", action="store_true", help="Exportar apenas laudos aprovados")
    args = parser.parse_args()

    if args.formato == "csv":
        total = exportar_prontuarios_csv(args.saida, crm=args.crm, apenas_aprovados=args.aprovados)
    else:
        total = exportar_prontuarios_json(args.saida, crm=args.crm, apenas_aprovados=args.aprovados)

    print(f"✅ Exportados {total} prontuários com sucesso para {args.saida}")


if __name__ == "__main__":
    main()
