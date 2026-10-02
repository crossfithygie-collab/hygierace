#!/usr/bin/env python3
"""build_timeline.py — la timeline du chef d'orchestre, Hygie Race 4.

Un document imprimable qui tient le fil de la journée : pour chaque vague,
l'heure d'échauffement, d'appel et de départ, puis couloir par couloir la
catégorie, l'équipe, les athlètes et le juge. Entre deux vagues, et c'est le
cœur du document, la liste des charges à changer, uniquement celles qui
changent vraiment.

    python3 build_timeline.py    -> race4-timeline.html
"""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLANNING = HERE / "planning_juges.json"
CATEGORIES = HERE / "categories_lanes.json"
SORTIE = HERE / "race4-timeline.html"

# Wall ball, deadlift, kettlebell, haltère. Le solo prend les charges du duo.
CHARGES = {
    "FF OPEN": ("4", "39", "12", "10"),
    "FF PRO": ("6", "52", "16", "15"),
    "HH OPEN": ("6", "52", "16", "15"),
    "HH PRO": ("9", "61", "24", "20"),
    "HF MIXTE": ("6", "52", "16", "15"),
    "HOMME OPEN": ("6", "52", "16", "15"),
    "HOMME PRO": ("9", "61", "24", "20"),
    "FEMME OPEN": ("4", "39", "12", "10"),
    "FEMME PRO": ("6", "52", "16", "15"),
}
NOMS = ("Wall ball", "Deadlift", "Kettlebell", "Haltère")

CSS = """
 @page{size:A4 portrait;margin:10mm}
 *{box-sizing:border-box;margin:0}
 body{font-family:Archivo,Helvetica,Arial,sans-serif;color:#000;background:#fff;
   font-size:9.6pt;line-height:1.3}
 h1{font-size:19pt;font-weight:900;letter-spacing:-.4pt;line-height:1}
 h1 small{display:block;font-size:7.6pt;font-weight:800;letter-spacing:1.8pt;
   text-transform:uppercase;margin-bottom:3pt}
 .intro{border-bottom:2.5pt solid #000;padding-bottom:6pt;margin-bottom:9pt;
   display:flex;justify-content:space-between;align-items:flex-end}
 .intro p{font-size:8.6pt;text-align:right;line-height:1.4;max-width:78mm}
 .vague{border:1.2pt solid #000;margin-bottom:7pt;page-break-inside:avoid}
 .vh{display:flex;align-items:center;gap:8pt;background:#000;color:#fff;
   padding:4pt 7pt}
 .vh b{font-size:13pt;font-weight:900}
 .vh u{text-decoration:none;font-size:8.4pt;font-weight:800;letter-spacing:1pt;
   text-transform:uppercase}
 .vh .h{margin-left:auto;font-size:8.6pt;font-weight:700;text-align:right}
 .vh .h b{font-size:13pt;display:inline}
 table{width:100%;border-collapse:collapse;font-size:9pt}
 th{font-size:6.8pt;font-weight:800;letter-spacing:.7pt;text-transform:uppercase;
   text-align:left;padding:3pt 6pt;border-bottom:.8pt solid #000;color:#333}
 td{padding:3.4pt 6pt;border-bottom:.5pt solid #bbb;vertical-align:top}
 tr:last-child td{border-bottom:0}
 td.l{font-weight:900;font-size:11pt;width:9mm;text-align:center}
 td.c{font-weight:800;width:24mm;font-size:8.4pt}
 td.e{font-weight:800}
 td.e span{display:block;font-weight:400;font-size:8.2pt;color:#333}
 td.j{width:38mm;font-size:8.6pt}
 .chg{border:1.2pt solid #000;background:#000;color:#fff;padding:5pt 8pt;
   margin-bottom:7pt;page-break-inside:avoid}
 .chg u{text-decoration:none;display:block;font-size:7.4pt;font-weight:800;
   letter-spacing:1.4pt;text-transform:uppercase;margin-bottom:3pt}
 .chg b{font-size:10.4pt;font-weight:900}
 .chg ul{margin:3pt 0 0 0;padding-left:13pt}
 .chg li{font-size:9.4pt;margin-bottom:1.5pt}
 .rien{border:1pt dashed #777;color:#333;padding:4pt 8pt;margin-bottom:7pt;
   font-size:8.8pt;page-break-inside:avoid}
 .rien b{font-weight:900}
 .pied{margin-top:8pt;border-top:1pt solid #000;padding-top:5pt;font-size:8pt;
   color:#333;line-height:1.45}
"""


def charges_de(cat: str) -> tuple:
    c = (cat or "").upper().strip()
    return CHARGES.get(c, CHARGES.get(c.replace("SOLO ", ""), ("?", "?", "?", "?")))


def changements(avant: dict, apres: dict) -> list[str]:
    """Ce qu'il faut toucher entre deux vagues, et rien d'autre."""
    lignes = []
    for lane in sorted(set(avant) | set(apres)):
        a, b = avant.get(lane), apres.get(lane)
        if not b:
            continue                      # couloir qui se vide : rien à préparer
        nb = charges_de(b)
        if not a:
            lignes.append(f"Couloir {lane} : monter {b} — "
                          + ", ".join(f"{n} {v} kg" for n, v in zip(NOMS, nb)))
            continue
        na = charges_de(a)
        quoi = [f"{n} {va} → <b>{vb} kg</b>"
                for n, va, vb in zip(NOMS, na, nb) if va != vb]
        if quoi:
            lignes.append(f"Couloir {lane} : {a} → {b} — " + ", ".join(quoi))
    return lignes


def main() -> None:
    plan = json.loads(PLANNING.read_text(encoding="utf-8"))
    cats = json.loads(CATEGORIES.read_text(encoding="utf-8"))

    def cat_de(n: int, lane: int) -> str:
        return (cats.get(f"{n}-{lane}") or {}).get("cat") or ""

    blocs, precedent = [], {}
    for h in plan["heats"]:
        lanes = sorted(h.get("lanes") or [], key=lambda x: x["lane"])
        actuel = {l["lane"]: cat_de(h["n"], l["lane"]) for l in lanes}

        chg = changements(precedent, actuel) if precedent else []
        if precedent:
            if chg:
                blocs.append(
                    '<div class="chg"><u>Avant la vague %d &middot; &eacute;chauffement %s</u>'
                    '<b>Changements de mat&eacute;riel</b><ul>%s</ul></div>'
                    % (h["n"], h.get("warmup", ""),
                       "".join(f"<li>{c}</li>" for c in chg)))
            else:
                blocs.append(
                    '<div class="rien"><b>Avant la vague %d : aucun changement '
                    'de charge.</b> M&ecirc;mes charges que la vague pr&eacute;c&eacute;dente, '
                    'on remet seulement les couloirs en ordre.</div>' % h["n"])

        rangs = []
        for l in lanes:
            c = cat_de(h["n"], l["lane"])
            wb, dl, kb, db = charges_de(c)
            ath = " &middot; ".join(html.escape(a) for a in (l.get("athletes") or []))
            rangs.append(
                f'<tr><td class="l">{l["lane"]}</td>'
                f'<td class="c">{html.escape(c)}<br>'
                f'<span style="font-weight:400;font-size:7.6pt">{wb}/{dl}/{kb}/{db} kg</span></td>'
                f'<td class="e">{html.escape(l.get("equipe") or "")}'
                f'<span>{ath}</span></td>'
                f'<td class="j">{html.escape(l.get("juge") or "")}</td></tr>')

        blocs.append(f"""
<div class="vague">
  <div class="vh"><b>VAGUE {h['n']}</b><u>{html.escape(h['division'])}</u>
    <span class="h">&eacute;chauffement {h.get('warmup','')} &middot;
      appel {h.get('call','')} &middot; d&eacute;part <b>{h['debut']}</b> &middot;
      fin {h['fin']}</span></div>
  <table><thead><tr><th>Lane</th><th>Cat&eacute;gorie et charges</th>
    <th>&Eacute;quipe et athl&egrave;tes</th><th>Juge</th></tr></thead>
  <tbody>{''.join(rangs)}</tbody></table>
</div>""")
        precedent = actuel

    total = sum(len(h.get("lanes") or []) for h in plan["heats"])
    SORTIE.write_text(f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Timeline · Hygie Race 4</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;700;800;900&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<div class="intro">
  <h1><small>Hygie Race 4 &middot; dimanche 4 octobre 2026</small>Timeline</div>
  <p>{len(plan['heats'])} vagues, {total} couloirs, de 8h00 &agrave; 13h35.<br>
  Chaque vague part 45 minutes apr&egrave;s la pr&eacute;c&eacute;dente.
  Time cap 80 minutes.</p>
</div>
{''.join(blocs)}
<div class="pied">Les charges sont not&eacute;es dans l'ordre wall ball / deadlift /
kettlebell / halt&egrave;re. Un couloir se pr&eacute;pare pendant l'&eacute;chauffement
de la vague suivante, jamais apr&egrave;s l'appel. Une vague appel&eacute;e part
&agrave; l'heure, sans les absents.</div>
</body></html>""", encoding="utf-8")
    print(f"timeline ecrite dans {SORTIE.name}")


if __name__ == "__main__":
    main()
