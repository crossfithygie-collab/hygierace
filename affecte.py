#!/usr/bin/env python3
"""Affecte un juge sur une lane du planning : affecte.py "Nom" heat lane"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parent / "planning_juges.json"
nom, heat, lane = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
d = json.loads(P.read_text(encoding="utf-8"))
for h in d["heats"]:
    if h["n"] != heat:
        continue
    for l in h["lanes"]:
        if l["lane"] == lane:
            avant = l["juge"]
            l["juge"] = nom
            P.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"HEAT {heat} lane {lane} : {avant} -> {nom}  ({l.get('equipe','')})")
            raise SystemExit
sys.exit("lane introuvable")
