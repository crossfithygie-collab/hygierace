#!/usr/bin/env python3
"""build_feuilles.py — les feuilles de jugement de la Hygie Race 4.

Une page A4 par couloir, prête à imprimer en noir et blanc, construite depuis
planning_juges.json : le juge, la lane, le heat, la division, l'équipe et ses
athlètes y sont déjà imprimés. Le juge n'a plus qu'à barrer et à signer.

    python3 build_feuilles.py        -> race4-feuilles.html
"""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "planning_juges.json"
SORTIE = HERE / "race4-feuilles.html"

# Les charges, pour que le juge les ait sous les yeux sans ouvrir le rulebook.
CHARGES = {
    "FF OPEN": ("4 kg", "39 kg", "12 kg", "10 kg"),
    "FF PRO": ("6 kg", "52 kg", "16 kg", "15 kg"),
    "HH OPEN": ("6 kg", "52 kg", "16 kg", "15 kg"),
    "HH PRO": ("9 kg", "61 kg", "24 kg", "20 kg"),
    "HF MIXTE": ("6 kg", "52 kg", "16 kg", "15 kg"),
}

STATIONS = [
    ("1", "Wall ball shots", "cible 3 m H / 2,70 m F", "reps"),
    ("2", "SkiErg", "1000 m", "machine"),
    ("3", "Deadlifts", "disques au sol, pas de rebond", "reps"),
    ("4", "Rameur", "1000 m", "machine"),
    ("5", "Burpees over the line", "poitrine et cuisses au sol, saut 2 pieds", "reps"),
    ("6", "Bike erg", "2000 m", "machine"),
    ("7", "Kettlebell swings american", "bras tendus au-dessus de la tete", "reps"),
    ("8", "DB box step-ups alternes", "halt\u00e8re sur la nuque, box 50 cm", "reps"),
]

CSS = """
 @page{size:A4 portrait;margin:9mm}
 *{box-sizing:border-box;margin:0}
 body{font-family:Archivo,Helvetica,Arial,sans-serif;color:#000;background:#fff;
   font-size:9.4pt;line-height:1.25}
 .feuille{page-break-after:always;height:279mm;display:flex;flex-direction:column}
 .feuille:last-child{page-break-after:auto}
 .haut{display:flex;justify-content:space-between;align-items:flex-start;
   border-bottom:2.5pt solid #000;padding-bottom:4pt}
 .titre{font-size:15pt;font-weight:900;letter-spacing:-.3pt;line-height:1}
 .titre small{display:block;font-size:7.4pt;font-weight:800;letter-spacing:1.6pt;
   text-transform:uppercase;margin-bottom:2pt}
 .repere{text-align:right;font-size:8.6pt;font-weight:800;line-height:1.35}
 .repere b{font-size:17pt;display:block;line-height:1.1;min-width:16mm;border-bottom:1pt solid #000}
 .qui{display:flex;gap:7pt;margin:6pt 0}
 .case{flex:1;border:1pt solid #000;padding:4pt 6pt;min-height:17mm}
 .case u{display:block;font-size:7pt;font-weight:800;letter-spacing:1.1pt;
   text-transform:uppercase;text-decoration:none;margin-bottom:2pt}
 .case b{font-size:11pt;font-weight:900;display:block;line-height:1.2}
 .case span{font-size:9pt;display:block}
 .charges{display:flex;gap:0;border:1pt solid #000;margin-bottom:6pt}
 .charges div{flex:1;padding:3pt 5pt;border-right:1pt solid #000;text-align:center}
 .charges div:last-child{border-right:0}
 .charges u{display:block;font-size:6.6pt;font-weight:800;letter-spacing:.8pt;
   text-transform:uppercase;text-decoration:none}
 .charges b{font-size:11pt;font-weight:900}
 .station{border:1pt solid #000;border-bottom:0;padding:3pt 5pt}
 .station:last-of-type{border-bottom:1pt solid #000}
 .sh{display:flex;align-items:baseline;gap:5pt;margin-bottom:2.5pt}
 .sh i{font-style:normal;font-weight:900;font-size:10.5pt;background:#000;color:#fff;
   width:13pt;height:13pt;display:inline-flex;align-items:center;justify-content:center;
   border-radius:2pt;flex:none}
 .sh b{font-size:10pt;font-weight:900}
 .sh em{font-style:normal;font-size:7.6pt;color:#333;margin-left:auto;text-align:right}
 .grille{display:grid;grid-template-columns:repeat(25,1fr);gap:0;
   border-left:.5pt solid #999;border-top:.5pt solid #999}
 .grille span{border-right:.5pt solid #999;border-bottom:.5pt solid #999;
   text-align:center;font-size:5.6pt;color:#555;padding:1.1pt 0}
 .grille span:nth-child(5n){border-right:1pt solid #000}
 .machine{display:flex;align-items:center;gap:6pt;padding:1pt 0}
 .machine .sh{margin:0;flex:none}
 .machine .trait{flex:1;border-bottom:1pt dotted #000;height:11pt}
 .bas{margin-top:auto;padding-top:6pt;border-top:2.5pt solid #000}
 .score{display:flex;gap:7pt;margin-bottom:5pt}
 .score div{flex:1;border:1.5pt solid #000;padding:4pt 6pt;height:17mm}
 .score u{display:block;font-size:7pt;font-weight:800;letter-spacing:1.1pt;
   text-transform:uppercase;text-decoration:none}
 .score em{font-style:normal;font-size:7.2pt;color:#444}
 .sign{display:flex;gap:7pt}
 .sign div{flex:1;border:1pt solid #000;height:17mm;padding:3pt 6pt}
 .rappel{font-size:7.2pt;color:#333;margin-top:4pt;line-height:1.35}
"""


def grille(n: int) -> str:
    """Les reps a barrer, par paquets de cinq pour compter d'un coup d'oeil."""
    return ('<div class="grille">'
            + "".join(f"<span>{i}</span>" for i in range(1, n + 1))
            + "</div>")


def charges_de(division: str) -> tuple:
    d = division.upper()
    for cle in ("HH PRO", "FF PRO", "HH OPEN", "FF OPEN", "HF MIXTE"):
        if cle in d:
            return CHARGES[cle]
    return ("selon categorie",) * 4


def feuille(heat: dict, lane: dict) -> str:
    wb, dl, kb, db = charges_de(heat["division"])
    ath = lane.get("athletes") or []
    equipe = lane.get("equipe") or ""
    noms = " \u00b7 ".join(html.escape(a) for a in ath) if ath else "&nbsp;"
    club = lane.get("club") or ""

    morceaux = []
    for num, nom, note, genre in STATIONS:
        tete = (f'<div class="sh"><i>{num}</i><b>{nom}</b>'
                f'<em>{note}</em></div>')
        if genre == "reps":
            morceaux.append(f'<div class="station">{tete}{grille(100)}</div>')
        else:
            morceaux.append(
                f'<div class="station"><div class="machine">{tete}'
                f'<span style="font-size:7.4pt">termin\u00e9 \u25a1 &nbsp; '
                f'reste :</span><span class="trait"></span>'
                f'<span style="font-size:7.4pt">m</span></div></div>')

    return f"""
<div class="feuille">
  <div class="haut">
    <div class="titre"><small>Hygie Race 4 &middot; 4 octobre 2026</small>
      Feuille de jugement</div>
    <div class="repere">HEAT <b>&nbsp;</b>
      LANE <b>&nbsp;</b></div>
  </div>

  <div class="qui">
    <div class="case"><u>&Eacute;quipe ou athl&egrave;te</u></div>
    <div class="case" style="flex:.7"><u>Juge</u></div>
    <div class="case" style="flex:.55"><u>Cat&eacute;gorie</u></div>
  </div>

  <div class="charges">
    <div><u>Wall ball</u><b>&nbsp;</b></div>
    <div><u>Deadlift</u><b>&nbsp;</b></div>
    <div><u>Kettlebell</u><b>&nbsp;</b></div>
    <div><u>DB step-up</u><b>&nbsp;</b></div>
    <div><u>Run</u><b>200 m / 3 min</b></div>
  </div>

  {"".join(morceaux)}

  <div class="bas">
    <div class="score">
      <div><u>Temps final</u><em>si la ligne est franchie avant 80:00</em></div>
      <div><u>Au cap : reps manquantes</u><em>10 m non faits = 1 rep</em></div>
    </div>
    <div class="sign">
      <div><u style="font-size:7pt;font-weight:800;letter-spacing:1.1pt;
        text-transform:uppercase;text-decoration:none">Signature athl&egrave;te</u></div>
      <div><u style="font-size:7pt;font-weight:800;letter-spacing:1.1pt;
        text-transform:uppercase;text-decoration:none">Signature juge</u></div>
    </div>
    <p class="rappel">Au bip des 3 minutes : note o&ugrave; en est ton athl&egrave;te.
      Une rep non termin&eacute;e au bip ne compte pas. Sur les machines, l'&eacute;cran
      ne se remet jamais &agrave; z&eacute;ro. Une rep refus&eacute;e se refait.
      R&eacute;clamation possible dans les 10 minutes qui suivent le heat, aupr&egrave;s
      du head judge.</p>
  </div>
</div>"""


def main() -> None:
    d = json.loads(SOURCE.read_text(encoding="utf-8"))
    besoin = sum(len(h.get("lanes") or []) for h in d["heats"])
    # Autant de feuilles vierges que de couloirs, plus dix de rabiot pour les
    # changements du matin.
    modele = feuille(d["heats"][0], (d["heats"][0].get("lanes") or [{}])[0])
    pages = [modele] * (besoin + 10)
    SORTIE.write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Feuilles de jugement · Hygie Race 4</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;800;900&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>{"".join(pages)}</body></html>""",
                      encoding="utf-8")
    print(f"{len(pages)} feuilles ecrites dans {SORTIE.name}")


if __name__ == "__main__":
    main()
