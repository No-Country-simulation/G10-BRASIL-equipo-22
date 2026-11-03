#!/usr/bin/env python3
"""
MediFlow (Equipo 22) — Atribuição Automática de Assignees às Issues no GitHub
Mapeia as labels de persona para os usuários oficiais dos 4 integrantes da equipe.
"""

import json
import subprocess
import sys

REPO = "No-Country-simulation/G10-BRASIL-equipo-22"

MAPPING = {
    "persona:carlos-sre-ia": "magnomct",
    "persona:fernando-nexus": "FSzekut",
    "persona:helder-data-oci": "HelderAmaralConsult",
    "persona:alessandro-app": "superjonic",
}


def main():
    print(f"🏥 Consultando issues do repositório {REPO}...")
    cmd = [
        "gh", "issue", "list",
        "--repo", REPO,
        "--limit", "100",
        "--json", "number,title,labels,assignees",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    issues = json.loads(res.stdout)

    print(f"Total de issues encontradas: {len(issues)}")

    updated = 0
    skipped = 0

    for issue in issues:
        number = issue["number"]
        labels = [l["name"] for l in issue.get("labels", [])]
        assignees = [a["login"] for a in issue.get("assignees", [])]

        target_user = None
        target_persona = None
        for lbl in labels:
            if lbl in MAPPING:
                target_user = MAPPING[lbl]
                target_persona = lbl
                break

        if not target_user:
            continue

        if target_user in assignees:
            skipped += 1
            continue

        print(f"-> Atribuindo issue #{number} ({target_persona}) para @{target_user}...")
        edit_cmd = [
            "gh", "issue", "edit", str(number),
            "--repo", REPO,
            "--add-assignee", target_user,
        ]
        subprocess.run(edit_cmd, capture_output=True, text=True, check=True)
        updated += 1

    print("\n" + "=" * 60)
    print(f"✅ Concluído! {updated} issues atualizadas, {skipped} já estavam atribuídas.")
    print("=" * 60)


if __name__ == "__main__":
    main()

