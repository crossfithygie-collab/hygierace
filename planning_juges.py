#!/usr/bin/env python3
"""Construit le planning des juges de la Hygie Race 4 et l'écrit dans
planning_juges.json (lu ensuite par build_juges.py).

Règles appliquées :
  - un juge ne juge pas le heat où il concourt, et il est libre 40 min avant
    (échauffement + call room) ;
  - au moins PAUSE_MINI minutes entre la fin d'un heat jugé et le début du suivant ;
  - indisponibilités individuelles (heure d'arrivée) ;
  - charge répartie au plus juste ; les lanes non couvertes restent « À pourvoir ».
"""
import itertools
import json
from pathlib import Path

HEATS = {1: (480, 560), 2: (525, 605), 3: (565, 645), 4: (610, 690),
         5: (650, 730), 6: (705, 785), 7: (735, 815)}
DIVISIONS = {1: "FF OPEN", 2: "FF OPEN - FF PRO", 3: "HF MIXTE", 4: "HF MIXTE",
             5: "HF MIXTE - Homme Open", 6: "HH OPEN", 7: "HH PRO"}
LANES = {1: 6, 2: 4, 3: 6, 4: 6, 5: 6, 6: 6, 7: 6}
PAUSE_MINI = 20
A_POURVOIR = "À pourvoir"

JUGES = ["Alex", "Amélie Lorek", "Améline Hego", "Cédric Degand", "Florian Carette",
         "Hélène Guaguere", "Jordann Chmielewski", "Justine Hoffmann", "Laëtitia Debruyne",
         "Luc Choteau", "Léo de Beaurepaire", "Marine", "Nathalie Destrebecq",
         "Pierre Francois", "Tapio"]
COURT = {"Florian Carette": 6, "Léo de Beaurepaire": 6, "Cédric Degand": 6}
PAS_AVANT = {"Amélie Lorek": 565, "Tapio": 540}        # minutes depuis minuit


def hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def possible(j, h):
    if COURT.get(j) == h:
        return False
    if j in COURT and HEATS[h][1] > HEATS[COURT[j]][0] - 40:
        return False
    return HEATS[h][0] >= PAS_AVANT.get(j, 0)


def compatible(h1, h2):
    a, b = sorted([HEATS[h1], HEATS[h2]])
    return b[0] - a[1] >= PAUSE_MINI


def meilleure_combi(j):
    """La plus grande série de heats jugeables par j, sans enchaînement."""
    dispo = [h for h in HEATS if possible(j, h)]
    for n in range(len(dispo), 0, -1):
        combis = [c for c in itertools.combinations(dispo, n)
                  if all(compatible(a, b) for a, b in itertools.combinations(c, 2))]
        if combis:
            # à taille égale, on préfère celle qui couvre les heats les plus chargés
            return max(combis, key=lambda c: sum(LANES[h] for h in c))
    return ()


def combis_possibles(j):
    """Toutes les séries de heats que j peut tenir, sans enchaînement."""
    dispo = [h for h in HEATS if possible(j, h)]
    out = []
    for n in range(len(dispo), 0, -1):
        out += [c for c in itertools.combinations(dispo, n)
                if all(compatible(a, b) for a, b in itertools.combinations(c, 2))]
    return out


def main():
    import random
    combis = {j: combis_possibles(j) for j in JUGES}

    def tirage(graine, mode):
        """Chaque juge prend, à son tour, la série qui bouche le plus de trous."""
        rnd = random.Random(graine)
        besoin = dict(LANES)
        ordre = JUGES[:]
        rnd.shuffle(ordre)
        # les juges les plus contraints choisissent en premier
        ordre.sort(key=lambda j: len(combis[j]))
        pris = {}
        for j in ordre:
            if mode == 0:      # priorité au nombre de trous bouchés
                cle = lambda c: (sum(1 for h in c if besoin[h] > 0), len(c), rnd.random())
            else:              # priorité aux heats les plus découverts
                cle = lambda c: (sum(besoin[h] for h in c if besoin[h] > 0),
                                 sum(1 for h in c if besoin[h] > 0), rnd.random())
            meilleur = max(combis[j], key=cle)
            pris[j] = meilleur
            for h in meilleur:
                if besoin[h] > 0:
                    besoin[h] -= 1
        plan = {h: [] for h in HEATS}
        for j, cs in pris.items():
            for h in cs:
                if len(plan[h]) < LANES[h]:
                    plan[h].append(j)
        for h in HEATS:
            while len(plan[h]) < LANES[h]:
                plan[h].append(A_POURVOIR)
        return plan, sum(1 for h in plan for n in plan[h] if n == A_POURVOIR)

    def couverture(choix):
        """Lanes couvertes par un dictionnaire juge -> série de heats."""
        cpt = {h: 0 for h in HEATS}
        for cs in choix.values():
            for h in cs:
                cpt[h] += 1
        return sum(min(cpt[h], LANES[h]) for h in HEATS), cpt

    def depuis_plan(plan):
        c = {j: tuple(h for h in sorted(HEATS) if j in plan[h]) for j in JUGES}
        return {j: v for j, v in c.items()}

    best_choix, best_couv = None, -1
    for g in range(4000):
        plan, _ = tirage(g, g % 2)
        choix = depuis_plan(plan)
        # amélioration locale : on change la série d'un juge si ça couvre plus
        amelioré = True
        while amelioré:
            amelioré = False
            for j in JUGES:
                actuel, _ = couverture(choix)
                for c in combis[j]:
                    if c == choix[j]:
                        continue
                    test = dict(choix); test[j] = c
                    v, _ = couverture(test)
                    if v > actuel:
                        choix, actuel, amelioré = test, v, True
        v, _ = couverture(choix)
        if v > best_couv:
            best_choix, best_couv = choix, v
            if v == sum(LANES.values()):
                break

    plan = {h: [] for h in HEATS}
    for j, cs in sorted(best_choix.items()):
        for h in cs:
            if len(plan[h]) < LANES[h]:
                plan[h].append(j)
    for h in HEATS:
        while len(plan[h]) < LANES[h]:
            plan[h].append(A_POURVOIR)

    data = {
        "evenement": "Hygie Race 4", "date": "dimanche 4 octobre 2026",
        "horaire": "7h30 à 13h30", "pause_mini": PAUSE_MINI,
        "heats": [{"n": h, "division": DIVISIONS[h],
                   "debut": hhmm(HEATS[h][0]), "fin": hhmm(HEATS[h][1]),
                   "warmup": hhmm(HEATS[h][0] - 25), "call": hhmm(HEATS[h][0] - 5),
                   "lanes": [{"lane": i + 1, "juge": n} for i, n in enumerate(plan[h])]}
                  for h in sorted(HEATS)],
        "athletes": {j: h for j, h in COURT.items()},
    }
    Path(__file__).with_name("planning_juges.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    manque = sum(1 for h in plan for n in plan[h] if n == A_POURVOIR)
    print(f"planning écrit : {sum(LANES.values())} lanes, {manque} à pourvoir")
    for j in sorted(JUGES):
        hs = [h for h in sorted(HEATS) if j in plan[h]]
        print(f"  {j:22} {len(hs)} heats : {', '.join('H' + str(h) for h in hs) or '—'}"
              + (f"   (court le heat {COURT[j]})" if j in COURT else ""))
    for h in sorted(HEATS):
        vides = [i + 1 for i, n in enumerate(plan[h]) if n == A_POURVOIR]
        if vides:
            print(f"  HEAT {h} : lanes à pourvoir {vides}")


if __name__ == "__main__":
    main()
