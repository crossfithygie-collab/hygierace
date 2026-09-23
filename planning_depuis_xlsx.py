#!/usr/bin/env python3
"""Construit planning_juges.json À PARTIR DU FICHIER DE JEREMY (juges + athlètes).

On garde ses affectations telles quelles ; seules les cases impossibles sont
libérées : un juge ne peut pas juger pendant sa propre course (ni pendant son
échauffement, 25 min avant).

    python3 planning_depuis_xlsx.py <planning juges .xlsx> <planning athlètes .xlsx>
"""
import json
import sys
from pathlib import Path

import openpyxl

ICI = Path(__file__).resolve().parent
A_POURVOIR = "À pourvoir"
FUSION = {"Florent": "Florian Carette", "Léo": "Léo de Beaurepaire",
          "HOFFMANN Justine": "Justine Hoffmann", "Laetitia debruyne": "Laëtitia Debruyne",
          "Cedric Degand": "Cédric Degand"}
COURT = {"Florian Carette": 6, "Léo de Beaurepaire": 6, "Cédric Degand": 6}
AVANT_COURSE = 25          # minutes de libération avant l'échauffement


def mins(t):
    h, m = str(t)[:5].split(":")
    return int(h) * 60 + int(m)


def nom(n):
    n = str(n or "").strip()
    return FUSION.get(n, n)


def lire_juges(src):
    ws = openpyxl.load_workbook(src, data_only=True)["planning - volunteers"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    g = {str(r[0]).strip(): [(str(x).strip() if x else "") for x in r[1:8]]
         for r in rows[1:] if r and r[0]}
    heats = {}
    for i in range(7):
        debut, fin = [mins(x) for x in g["START-END"][i].split(" - ")]
        heats[i + 1] = {
            "n": i + 1, "division": g["DIVISIONS"][i],
            "debut": g["START-END"][i].split(" - ")[0][:5],
            "fin": g["START-END"][i].split(" - ")[1][:5],
            "warmup": str(g["WARM-UP"][i])[:5], "call": str(g["CALL ROOM"][i])[:5],
            "_debut": debut, "_fin": fin, "lanes": [],
        }
    for cle, vals in g.items():
        if not cle.upper().startswith("LANE"):
            continue
        lane = int(cle.split()[-1])
        for i, v in enumerate(vals):
            if v:
                heats[i + 1]["lanes"].append({"lane": lane, "juge": nom(v)})
    return heats


def lire_athletes(src):
    ws = openpyxl.load_workbook(src, data_only=True)["planning - athletes"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    out = {}
    for i, r in enumerate(rows):
        t = str(r[0] or "").strip().upper()
        if not t.startswith("LANE"):
            continue
        lane = int(t.split()[-1])
        eq = rows[i + 1] if i + 1 < len(rows) else []
        at = rows[i + 2] if i + 2 < len(rows) else []
        for h in range(1, 8):
            e = str((eq[h] if h < len(eq) else "") or "").strip()
            a = str((at[h] if h < len(at) else "") or "").strip()
            if not e and not a:
                continue
            bloc = [x.strip() for x in e.split("\n") if x.strip()]
            out[(h, lane)] = {"equipe": bloc[0] if bloc else "",
                              "club": bloc[1] if len(bloc) > 1 else "",
                              "athletes": [x.strip() for x in a.split("\n") if x.strip()]}
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit("usage : planning_depuis_xlsx.py <juges.xlsx> <athletes.xlsx>")
    heats = lire_juges(sys.argv[1])
    infos = lire_athletes(sys.argv[2])

    liberees = []
    for h in heats.values():
        for l in h["lanes"]:
            j = l["juge"]
            if j in COURT:
                course = heats[COURT[j]]
                if h["n"] == COURT[j] or h["_fin"] > course["_debut"] - AVANT_COURSE:
                    liberees.append((j, h["n"], l["lane"]))
                    l["juge"] = A_POURVOIR
            l.update(infos.get((h["n"], l["lane"]), {}))
        h["lanes"].sort(key=lambda x: x["lane"])
        del h["_debut"], h["_fin"]

    data = {"evenement": "Hygie Race 4", "date": "dimanche 4 octobre 2026",
            "horaire": "7h30 à 13h30", "heats": [heats[i] for i in sorted(heats)],
            "athletes": COURT}
    (ICI / "planning_juges.json").write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    manque = [(h["n"], l["lane"]) for h in data["heats"] for l in h["lanes"]
              if l["juge"] == A_POURVOIR]
    print(f"planning repris du fichier : {sum(len(h['lanes']) for h in data['heats'])} lanes")
    print("libérées (juge en course) :", liberees)
    print("à pourvoir :", manque)


if __name__ == "__main__":
    main()
