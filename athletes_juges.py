#!/usr/bin/env python3
"""Ajoute au planning des juges qui ils vont juger : équipe, club et athlètes,
lus dans le planning athlètes (xlsx). Écrit dans planning_juges.json.

    python3 athletes_juges.py ~/Downloads/"Hygie Race 4 - ... - athletes - 23_09_2026.xlsx"
"""
import json
import sys
from pathlib import Path

import openpyxl

ICI = Path(__file__).resolve().parent
PLAN = ICI / "planning_juges.json"


def lire(src):
    """{(heat, lane): {equipe, club, athletes}} depuis la feuille athlètes."""
    ws = openpyxl.load_workbook(src, data_only=True)["planning - athletes"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    out = {}
    for i, r in enumerate(rows):
        titre = str(r[0] or "").strip().upper()
        if not titre.startswith("LANE"):
            continue
        lane = int(titre.split()[-1])
        equipes = rows[i + 1] if i + 1 < len(rows) else []
        athletes = rows[i + 2] if i + 2 < len(rows) else []
        for h in range(1, 8):
            eq = str((equipes[h] if h < len(equipes) else "") or "").strip()
            at = str((athletes[h] if h < len(athletes) else "") or "").strip()
            if not eq and not at:
                continue
            bloc = [x.strip() for x in eq.split("\n") if x.strip()]
            out[(h, lane)] = {
                "equipe": bloc[0] if bloc else "",
                "club": bloc[1] if len(bloc) > 1 else "",
                "athletes": [x.strip() for x in at.split("\n") if x.strip()],
            }
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if not src:
        sys.exit("usage : athletes_juges.py <planning athlètes .xlsx>")
    infos = lire(src)
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    n = 0
    for heat in data["heats"]:
        for l in heat["lanes"]:
            info = infos.get((heat["n"], l["lane"]))
            if info:
                l.update(info)
                n += 1
    PLAN.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{n} lanes enrichies (équipe, club, athlètes)")
    manque = [(h["n"], l["lane"]) for h in data["heats"] for l in h["lanes"] if not l.get("equipe")]
    if manque:
        print("sans équipe :", manque)


if __name__ == "__main__":
    main()
