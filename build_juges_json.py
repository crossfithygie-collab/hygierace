#!/usr/bin/env python3
"""Écrit race4-juges.html à partir de planning_juges.json (planning recalculé).

    python3 planning_juges.py && python3 build_juges_json.py
"""
import html
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
OUT = ICI / "race4-juges.html"
E = html.escape
A_POURVOIR = "À pourvoir"


def main():
    d = json.loads((ICI / "planning_juges.json").read_text(encoding="utf-8"))
    heats = d["heats"]
    athletes = d.get("athletes", {})

    # ---- tableau général --------------------------------------------------
    th = "".join(f'<th>HEAT {h["n"]}</th>' for h in heats)

    def ligne(titre, valeurs, cls=""):
        return (f'<tr class="{cls}"><th scope="row">{E(titre)}</th>'
                + "".join(f"<td>{v}</td>" for v in valeurs) + "</tr>")

    corps = ligne("Division", [E(h["division"]) for h in heats], "div")
    corps += ligne("Warm-up", [E(h["warmup"]) for h in heats])
    corps += ligne("Call room", [E(h["call"]) for h in heats])
    corps += ligne("Heat", [f'{E(h["debut"])} – {E(h["fin"])}' for h in heats], "heat")
    for i in range(6):
        vals = []
        for h in heats:
            nom = next((l["juge"] for l in h["lanes"] if l["lane"] == i + 1), "")
            vals.append(f'<span class="vide">{E(A_POURVOIR)}</span>' if nom == A_POURVOIR
                        else E(nom) if nom else "—")
        corps += ligne(f"Lane {i + 1}", vals, "lane")

    # ---- fiches par juge --------------------------------------------------
    par_juge = {}
    for h in heats:
        for l in h["lanes"]:
            if l["juge"] and l["juge"] != A_POURVOIR:
                par_juge.setdefault(l["juge"], []).append((h, l["lane"]))
    cartes = []
    for nom in sorted(par_juge, key=str.lower):
        li = "".join(
            f'<li><b>HEAT {h["n"]}</b> <span class="lane">Lane {lane}</span>'
            f'<span class="quand">{E(h["debut"])} – {E(h["fin"])}</span>'
            f'<span class="divi">{E(h["division"])}</span></li>'
            for h, lane in par_juge[nom])
        course = (f'<p class="rq">Tu cours le <b>heat {athletes[nom]}</b> : '
                  f'pas de jugement autour de ta course.</p>' if nom in athletes else "")
        cartes.append(f'<article class="juge" data-nom="{E(nom.lower())}">'
                      f'<h3>{E(nom)}</h3><ul>{li}</ul>{course}</article>')

    manque = sum(1 for h in heats for l in h["lanes"] if l["juge"] == A_POURVOIR)
    alerte = (f'<p class="alerte"><b>{manque} lanes sont encore à pourvoir.</b> Si tu peux '
              f'prendre un créneau de plus, dis-le à Jérémy : c\'est marqué « {A_POURVOIR} » '
              f'dans le tableau.</p>' if manque else "")

    page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Juges · Hygie Race 4</title>
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#1800AD">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,600;0,700;0,800;0,900;1,800;1,900&family=Permanent+Marker&display=swap" rel="stylesheet">
<link rel="stylesheet" href="race4.css?v=4">
<style>
  .juges-wrap{{max-width:980px;margin:0 auto;padding:34px 20px 90px;position:relative;z-index:2;}}
  .juges-wrap h1{{font-size:clamp(34px,9vw,54px);text-align:center;}}
  .intro{{text-align:center;color:var(--soft);font-size:14.5px;line-height:1.6;margin:18px auto 0;max-width:620px;}}
  .intro b{{color:#fff;}}
  .alerte{{max-width:620px;margin:18px auto 0;border:2px solid #fff;border-radius:12px;padding:13px 16px;
    text-align:center;font-size:13.5px;line-height:1.6;color:#fff;}}
  h2{{margin:44px 0 14px;font-weight:900;font-style:italic;font-size:15px;letter-spacing:2px;text-transform:uppercase;}}
  .scroll{{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1.5px solid var(--hair);border-radius:12px;background:var(--fill);}}
  table{{border-collapse:collapse;width:100%;min-width:760px;font-size:13px;}}
  th,td{{padding:9px 11px;text-align:left;border-bottom:1px solid var(--hair);white-space:nowrap;}}
  thead th{{font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--soft);}}
  th[scope=row]{{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--soft2);font-weight:800;}}
  tr.div td{{font-weight:900;font-style:italic;}}
  tr.heat td{{font-weight:800;}}
  .vide{{display:inline-block;border:1px dashed rgba(255,255,255,.55);border-radius:999px;padding:1px 9px;
    font-size:11px;font-weight:800;letter-spacing:.4px;text-transform:uppercase;color:var(--soft);}}
  .recherche{{display:block;width:100%;max-width:340px;margin:0 auto;padding:13px 16px;border-radius:999px;
    border:1.5px solid var(--hair);background:var(--fill);color:#fff;font:inherit;font-size:15px;text-align:center;}}
  .recherche::placeholder{{color:var(--soft2);}}
  .grille{{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));margin-top:16px;}}
  .juge{{border:1.5px solid var(--hair);border-radius:12px;padding:15px 17px;background:var(--fill);}}
  .juge h3{{margin:0 0 10px;font-weight:900;font-style:italic;font-size:17px;text-transform:uppercase;}}
  .juge ul{{list-style:none;margin:0;padding:0;}}
  .juge li{{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;padding:7px 0;border-top:1px solid var(--hair);font-size:13.5px;}}
  .juge li b{{font-weight:900;}}
  .lane{{font-size:11px;letter-spacing:.5px;text-transform:uppercase;border:1px solid var(--hair);border-radius:999px;padding:2px 8px;}}
  .quand{{color:#fff;font-weight:700;}}
  .divi{{width:100%;color:var(--soft2);font-size:11.5px;letter-spacing:.4px;text-transform:uppercase;}}
  .rq{{margin:10px 0 0;color:var(--soft);font-size:12.5px;line-height:1.5;}}
  .juge.cache{{display:none;}}
  .rappels{{margin-top:34px;border-left:3px solid #fff;padding:4px 0 4px 16px;color:var(--soft);font-size:14px;line-height:1.75;}}
  .rappels b{{color:#fff;}}
</style>
</head>
<body>
<div class="frame"><i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i></div>

<div class="juges-wrap">
  <div class="logo-wrap"><img class="logo" src="race4-logo.png" alt="RAC4 · CrossFit Hygie"></div>
  <h1>Planning des juges</h1>
  <p class="intro">{E(d["date"].capitalize())}, de <b>{E(d["horaire"])}</b>, à CrossFit Hygie.<br>
  Trouve ton nom ci-dessous : tu y vois tes heats, ta lane et tes horaires.</p>
  {alerte}

  <h2>Ton planning</h2>
  <input class="recherche" id="q" type="search" placeholder="Tape ton nom" autocomplete="off">
  <div class="grille" id="grille">
    {"".join(cartes)}
  </div>

  <h2>Le planning complet</h2>
  <div class="scroll">
    <table>
      <thead><tr><th></th>{th}</tr></thead>
      <tbody>{corps}</tbody>
    </table>
  </div>

  <div class="rappels">
    <b>Sois là 15 minutes avant ton premier heat</b>, briefing juges avant le heat 1.<br>
    Tu juges <b>une lane</b> : tu comptes les répétitions et tu valides les standards de ton athlète.<br>
    Un doute sur un mouvement : tu appelles le <b>head judge</b> (Baptiste ou Jérémy), jamais de décision dans le flou.<br>
    <b>Petit déjeuner offert au bar</b>, dispo toute la matinée.<br>
    Merci d'être là : sans vous, la course n'existe pas 💪
  </div>
</div>

<script>
  var q = document.getElementById('q');
  q.addEventListener('input', function () {{
    var v = q.value.trim().toLowerCase();
    document.querySelectorAll('.juge').forEach(function (c) {{
      c.classList.toggle('cache', v !== '' && c.dataset.nom.indexOf(v) === -1);
    }});
  }});
</script>
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"✓ {OUT.name} écrit : {len(par_juge)} juges, {manque} lanes à pourvoir")


if __name__ == "__main__":
    main()
