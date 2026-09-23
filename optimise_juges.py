#!/usr/bin/env python3
"""Répartit les juges sur les 40 lanes de la Hygie Race 4.

Règles :
  - jamais deux heats qui se chevauchent pour un même juge ;
  - les athlètes du heat 6 sont libres 25 min avant leur échauffement ;
  - affectations imposées (qui juge qui) respectées ;
  - charge la plus égale possible, et on couvre toutes les lanes.

    python3 optimise_juges.py <planning athlètes .xlsx>
"""
import json
import random
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
A_POURVOIR = "À pourvoir"

HEATS = {1: ("08:00", "09:20", "FF OPEN"), 2: ("08:45", "10:05", "FF OPEN - FF PRO"),
         3: ("09:25", "10:45", "HF MIXTE"), 4: ("10:10", "11:30", "HF MIXTE"),
         5: ("10:50", "12:10", "HF MIXTE - Homme Open"), 6: ("11:35", "12:55", "HH OPEN"),
         7: ("12:15", "13:35", "HH PRO")}
LANES = {1: 6, 2: 4, 3: 6, 4: 6, 5: 6, 6: 6, 7: 6}

JUGES = ["Alex", "Amélie Lorek", "Améline Hego", "Cédric Degand", "Elise Bailly",
         "Florian Carette", "Hélène Guaguere", "Jordann Chmielewski", "Justine Hoffmann",
         "Laëtitia Debruyne", "Luc Choteau", "Léo de Beaurepaire", "Marine Bar", "Mathias",
         "Nathalie Destrebecq", "Pierre Francois", "Romain De Bels", "Sarah Trenson"]
COURT = {"Florian Carette": 6, "Léo de Beaurepaire": 6, "Cédric Degand": 6}
# Demandes de Jeremy : qui juge qui (heat, lane) -> juge
IMPOSE = {(2, 1): "Romain De Bels",     # Pauline Monnier
          (5, 6): "Marine Bar"}          # Jean-Baptiste Loménech


def mins(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)


PLAGE = {n: (mins(a), mins(b)) for n, (a, b, _) in HEATS.items()}


def chevauche(a, b):
    x, y = sorted([PLAGE[a], PLAGE[b]])
    return y[0] < x[1]


def possible(j, n, deja):
    if COURT.get(j) == n:
        return False
    if j in COURT and PLAGE[n][1] > PLAGE[COURT[j]][0] - 25:
        return False
    return not any(chevauche(n, k) for k in deja)


def essai(graine):
    rnd = random.Random(graine)
    plan = {n: {} for n in HEATS}
    pris = {j: set() for j in JUGES}
    for (n, lane), j in IMPOSE.items():
        plan[n][lane] = j
        pris[j].add(n)
    # les heats les plus contraints d'abord : ceux avec le moins de candidats
    slots = [(n, lane) for n in HEATS for lane in range(1, LANES[n] + 1)
             if lane not in plan[n]]
    rnd.shuffle(slots)
    slots.sort(key=lambda s: len([j for j in JUGES if possible(j, s[0], pris[j])]))
    for n, lane in slots:
        cands = [j for j in JUGES if j not in plan[n].values() and possible(j, n, pris[j])]
        if not cands:
            plan[n][lane] = A_POURVOIR
            continue
        # le moins chargé d'abord, puis celui qui a le moins d'options restantes
        cands.sort(key=lambda j: (len(pris[j]),
                                  len([m for m in HEATS if possible(j, m, pris[j])]),
                                  rnd.random()))
        j = cands[0]
        plan[n][lane] = j
        pris[j].add(n)
    trous = sum(1 for n in plan for lane in plan[n] if plan[n][lane] == A_POURVOIR)
    charges = [len(v) for v in pris.values()]
    return plan, pris, trous, max(charges) - min(charges)


def main():
    meilleur = None
    for g in range(20000):
        plan, pris, trous, ecart = essai(g)
        cle = (trous, ecart)
        if meilleur is None or cle < meilleur[0]:
            meilleur = (cle, plan, pris)
            if cle == (0, 1):
                break
    (trous, ecart), plan, pris = meilleur
    print(f"lanes non couvertes : {trous} | écart de charge : {ecart}")

    infos = {}
    if len(sys.argv) > 1:
        import openpyxl
        ws = openpyxl.load_workbook(sys.argv[1], data_only=True)["planning - athletes"]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        for i, r in enumerate(rows):
            t = str(r[0] or "").strip().upper()
            if not t.startswith("LANE"):
                continue
            lane = int(t.split()[-1])
            eq, at = rows[i + 1], rows[i + 2]
            for h in range(1, 8):
                e = str((eq[h] if h < len(eq) else "") or "").strip()
                a = str((at[h] if h < len(at) else "") or "").strip()
                if e or a:
                    bloc = [x.strip() for x in e.split("\n") if x.strip()]
                    infos[(h, lane)] = {"equipe": bloc[0] if bloc else "",
                                        "club": bloc[1] if len(bloc) > 1 else "",
                                        "athletes": [x.strip() for x in a.split("\n") if x.strip()]}

    data = {"evenement": "Hygie Race 4", "date": "dimanche 4 octobre 2026",
            "horaire": "7h30 à 13h30", "athletes": COURT, "heats": []}
    for n in sorted(HEATS):
        debut, fin, div = HEATS[n]
        data["heats"].append({
            "n": n, "division": div, "debut": debut, "fin": fin,
            "warmup": f"{(PLAGE[n][0]-25)//60:02d}:{(PLAGE[n][0]-25)%60:02d}",
            "call": f"{(PLAGE[n][0]-5)//60:02d}:{(PLAGE[n][0]-5)%60:02d}",
            "lanes": [dict({"lane": lane, "juge": plan[n][lane]}, **infos.get((n, lane), {}))
                      for lane in sorted(plan[n])]})
    (ICI / "planning_juges.json").write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    for j in sorted(JUGES):
        hs = sorted(pris[j])
        print(f"  {j:22} {len(hs)} heats : {hs}" + (f"  (court le {COURT[j]})" if j in COURT else ""))


if __name__ == "__main__":
    main()
