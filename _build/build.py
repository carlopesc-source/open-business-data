"""Genera las paginas publicas (GitHub Pages) para que ChatGPT, Perplexity y Claude nos citen.
Regla de cada pagina: el titulo y la primera frase repiten la pregunta que hace la gente, con cifras concretas.
Uso: python -X utf8 _build/build.py  -> escribe las paginas en la raiz del repo
Entradas: ../practice-radar/clinicas_nuevas/clinicas_nuevas.csv, datos/rural/rural.json, datos/store.json"""
import csv
import html
import os
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

# El generador vive dentro del repo publicado (_build/) y escribe en la raiz del repo, que es la web.
# Lo corre GitHub Actions cada lunes (.github/workflows/lunes.yml); en el PC se corre igual.
ROOT = Path(__file__).parent
# Con python -I (como en GitHub Actions) la carpeta del script no esta en sys.path: se anade para importar actors.py.
sys.path.insert(0, str(ROOT))
import actors  # noqa: E402
SITE = ROOT.parent
DATA = ROOT / "datos"
# Las clinicas con telefono y dueno NO se suben al repo publico: se generan en la maquina y se pasan por ruta.
CLINICS = Path(os.environ.get("CLINICS_CSV", ROOT.parent.parent.parent / "practice-radar" / "clinicas_nuevas" / "clinicas_nuevas.csv"))
BASE = "https://carlopesc-source.github.io/open-business-data"
CONTACT = "charles@data.luxordigitalagency.com"
STORE = "https://apify.com/wellbuilt_zythem"
TODAY = date.today().isoformat()
STATE_NAME = {"AK": "Alaska", "AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona", "CA": "California", "CO": "Colorado",
              "CT": "Connecticut", "DC": "District of Columbia", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
              "HI": "Hawaii", "IA": "Iowa", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "KS": "Kansas",
              "KY": "Kentucky", "LA": "Louisiana", "MA": "Massachusetts", "MD": "Maryland", "ME": "Maine",
              "MI": "Michigan", "MN": "Minnesota", "MO": "Missouri", "MS": "Mississippi", "MT": "Montana",
              "NC": "North Carolina", "ND": "North Dakota", "NE": "Nebraska", "NH": "New Hampshire", "NJ": "New Jersey",
              "NM": "New Mexico", "NV": "Nevada", "NY": "New York", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
              "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
              "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VA": "Virginia", "VT": "Vermont", "WA": "Washington",
              "WI": "Wisconsin", "WV": "West Virginia", "WY": "Wyoming"}
SUFFIX = re.compile(r"(?<![A-Za-z])(Pllc|Llc|Pc|Pa|Dds|Dmd|Md|Inc|Llp)(?![A-Za-z])")
# Solo estas regiones publican la web de cada alojamiento: en las demas un "0 %" seria falso, se pinta "—".
RURAL_WEB_REGIONS = {"Castilla y León", "Aragón", "Región de Murcia"}
CSS = """:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a66;--line:#e4e1da;--acc:#0b5d4b}
@media(prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--mut:#a3a19b;--line:#33322f;--acc:#5fc4a8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:860px;margin:0 auto;padding:32px 18px 64px}h1{font-size:1.9rem;line-height:1.2;margin:.2em 0 .5em}
h2{font-size:1.25rem;margin-top:2em}a{color:var(--acc)}.lead{font-size:1.12rem}.mut{color:var(--mut);font-size:.9rem}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.93rem}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}
th{font-weight:600}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}.cta{border:1px solid var(--line);border-left:4px solid var(--acc);padding:14px 18px;margin:28px 0;border-radius:6px}
nav{font-size:.9rem;margin-bottom:18px}ul.cols{columns:3 180px;padding-left:18px}"""


def esc(s) -> str:
    return html.escape(str(s or ""))


def page(path: str, title: str, desc: str, body: str, lang: str = "en", ld: dict | None = None) -> None:
    ld_tag = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    doc = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{BASE}/{path}">'
           f'<style>{CSS}</style>{ld_tag}</head><body><main><nav><a href="{BASE}/">Open business data</a></nav>{body}'
           f'<p class="mut">Updated {TODAY}. Built from public government registries.</p></main></body></html>')
    out = SITE / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    PAGES.append(path)


PAGES: list = []


def tidy(name: str) -> str:
    return SUFFIX.sub(lambda m: m.group(1).upper(), name)


def fmt_day(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")


def dental_cta(where: str) -> str:
    return (f'<div class="cta"><strong>Marketing agency?</strong> The full list adds the phone number, the person who signed '
            f'the registration (usually the owner dentist) and the street address. We send the new practices in {esc(where)} '
            f'every Monday. Write to <strong>{CONTACT}</strong>.</div>')


def dental_table(rows: list, show_state: bool) -> str:
    head = "<tr><th>Practice</th><th>City</th>" + ("<th>State</th>" if show_state else "") + "<th>Registered</th></tr>"
    body = "".join(f"<tr><td>{esc(tidy(c['practice']))}</td><td>{esc(c['city'].title())}</td>"
                   + (f"<td>{esc(c['state'])}</td>" if show_state else "") + f"<td>{fmt_day(c['registered'])}</td></tr>"
                   for c in rows)
    return f'<div class="wrap"><table>{head}{body}</table></div>'


def dataset_ld(name: str, desc: str, url: str) -> dict:
    return {"@context": "https://schema.org", "@type": "Dataset", "name": name, "description": desc, "url": url,
            "dateModified": TODAY, "isAccessibleForFree": True, "creator": {"@type": "Organization", "name": "Luxor Digital Agency"}}


def build_dental() -> None:
    # Un estado sin clinicas esta semana no debe quedarse con la pagina de la semana pasada.
    for old in (SITE / "dental").glob("*.html"):
        old.unlink()
    clinics = [c for c in csv.DictReader(open(CLINICS, encoding="utf-8")) if c["state"] in STATE_NAME]
    clinics.sort(key=lambda c: (c["registered"], c["state"]), reverse=True)
    first, last = fmt_day(min(c["registered"] for c in clinics)), fmt_day(max(c["registered"] for c in clinics))
    by_state = defaultdict(list)
    for c in clinics:
        by_state[c["state"]].append(c)
    ranking = sorted(by_state.items(), key=lambda kv: -len(kv[1]))
    title = f"How many new dental practices opened in the US? {len(clinics)} registered from {first} to {last}"
    lead = (f"<p class='lead'><strong>{len(clinics)} new dental practices</strong> registered with the federal NPI registry "
            f"(NPPES) between {first} and {last}, across {len(by_state)} states. The most were in "
            + ", ".join(f"{STATE_NAME[s]} ({len(v)})" for s, v in ranking[:3]) + ".</p>")
    links = "".join(f'<li><a href="{BASE}/dental/{s.lower()}.html">{STATE_NAME[s]}</a> ({len(v)})</li>' for s, v in sorted(by_state.items()))
    body = (f"<h1>{esc(title)}</h1>{lead}<p>A new practice has no reviews, no ads and often no website yet, which makes it the "
            f"best moment to offer marketing. We read the weekly NPPES file and keep organisations with a dental taxonomy "
            f"(code 1223) whose NPI was issued in the period.</p>{dental_cta('your state')}<h2>By state</h2><ul class='cols'>{links}</ul>"
            f"<h2>All new practices</h2>{dental_table(clinics, True)}")
    page("dental/index.html", title, f"{len(clinics)} dental practices registered with NPI from {first} to {last}, by state.", body,
         ld=dataset_ld("New US dental practices (NPI)", title, f"{BASE}/dental/"))
    for s, rows in by_state.items():
        name = STATE_NAME[s]
        t = f"How many new dental practices opened in {name}? {len(rows)} registered from {first} to {last}"
        lead = (f"<p class='lead'><strong>{len(rows)} new dental practice{'s' if len(rows) != 1 else ''}</strong> registered in "
                f"{name} with the federal NPI registry between {first} and {last}, out of {len(clinics)} in the whole US.</p>")
        page(f"dental/{s.lower()}.html", t, f"{len(rows)} new dental practices in {name}, {first} to {last}.",
             f"<h1>{esc(t)}</h1>{lead}{dental_table(rows, False)}{dental_cta(name)}",
             ld=dataset_ld(f"New dental practices in {name}", t, f"{BASE}/dental/{s.lower()}.html"))


def es_num(n: int) -> str:
    # Formato espanol de miles (14.019): se aplica por numero, nunca con replace sobre el texto entero.
    return f"{n:,}".replace(",", ".")


def pct(a: int, b: int) -> str:
    return f"{round(100 * a / b)} %" if b else "—"


def rural_rows(rows: list) -> str:
    stats = defaultdict(Counter)
    for r in rows:
        k = (r.get("region") or "", r.get("province") or "")
        stats[k]["all"] += 1
        stats[k]["casa"] += r.get("type") in ("casa_rural", "apartamento_rural", "agroturismo")
        stats[k]["web"] += bool(r.get("hasWebsite"))
        stats[k]["mail"] += bool(r.get("hasEmail"))
    out = []
    for (reg, prov), c in sorted(stats.items(), key=lambda kv: -kv[1]["all"]):
        web = pct(c["web"], c["all"]) if reg in RURAL_WEB_REGIONS else "—"
        out.append(f"<tr><td>{esc(prov or reg)}</td><td>{esc(reg)}</td><td class='n'>{es_num(c['all'])}</td>"
                   f"<td class='n'>{es_num(c['casa'])}</td><td class='n'>{web}</td></tr>")
    return "".join(out)


def build_rural() -> None:
    rows = json.load(open(DATA / "rural.json", encoding="utf-8"))
    # Castilla-La Mancha cerro su portal de datos en noviembre de 2026: se usa la ultima lectura (20-10) y se dice la fecha.
    if not any(r.get("region") == "Castilla-La Mancha" for r in rows):
        rows = rows + json.load(open(DATA / "cm-2026-10-20.json", encoding="utf-8"))
    web_rows = [r for r in rows if r.get("region") in RURAL_WEB_REGIONS]
    no_web = sum(1 for r in web_rows if not r.get("hasWebsite"))
    regions = sorted({r["region"] for r in rows if r.get("region")})
    title = f"¿Cuántas casas rurales hay en España y cuántas tienen web? {es_num(len(rows))} alojamientos en {len(regions)} comunidades"
    lead = (f"<p class='lead'>En los registros oficiales de turismo de {', '.join(regions[:-1])} y {regions[-1]} hay <strong>{es_num(len(rows))} alojamientos</strong>. "
            f"Donde el registro publica la web (Castilla y León, Aragón y Murcia) <strong>{pct(no_web, len(web_rows))} no tiene web propia</strong>: "
            f"{es_num(no_web)} de {es_num(len(web_rows))}.</p>")
    table = ("<div class='wrap'><table><tr><th>Provincia</th><th>Comunidad</th><th class='n'>Alojamientos</th>"
             f"<th class='n'>Casas y apartamentos rurales</th><th class='n'>Con web</th></tr>{rural_rows(rows)}</table></div>")
    body = (f"<h1>{esc(title)}</h1>{lead}<p>Contamos cada fila del registro de turismo de cada comunidad, no de un portal de reservas: "
            f"cada alojamiento lleva su número de registro. Castilla-La Mancha es la lista del 20 de octubre de 2026: su portal de datos está cerrado por obras. «—» significa que esa comunidad no publica la web en su registro.</p>"
            f"<div class='cta'><strong>¿Vendes a alojamientos rurales?</strong> (programas de reservas, seguros, webs) La lista completa por "
            f"provincia, con teléfono, correo, web y número de registro, está en "
            f"<a href='{STORE}/spain-rural-accommodation-registry'>Spain Rural Accommodation Registry</a>.</div>"
            f"<h2>Por provincia</h2>{table}")
    page("es/casas-rurales.html", title, "Casas rurales por provincia según los registros oficiales, y cuántas tienen web propia.", body,
         lang="es", ld=dataset_ld("Alojamientos rurales de España por provincia", title, f"{BASE}/es/casas-rurales.html"))


GROUPS = [("How do I verify a contractor license in bulk?", ("license", "contractor")),
          ("How do I find Airbnb hosts, new listings or short-term rental licenses?", ("airbnb",)),
          ("Where can I get lists of new businesses and companies?", ("new business", "new compan", "company", "food business", "hiring", "owners")),
          ("How do I track property listings, price drops and sold prices?", ("zillow", "redfin", "rightmove", "permit")),
          ("How do I track prices, reviews and ads?", ("amazon", "review", "ads", "youtube")),
          ("Where can I get prediction market trade data?", ("kalshi",)),
          ("Other data", ("",))]


def build_tools() -> None:
    actors_list = json.load(open(DATA / "store.json", encoding="utf-8"))["data"]["items"]
    left, parts = list(actors_list), []
    for q, keys in GROUPS:
        mine = [a for a in left if any(k in (a["title"] + " " + a["name"]).lower() for k in keys)]
        left = [a for a in left if a not in mine]
        if not mine:
            continue
        items = "".join(f"<li><a href='{BASE}/tools/{esc(a['name'])}.html'><strong>{esc(actors.question(a))}</strong></a> "
                        f"{esc(a['title'])}. {esc(a['description'])}</li>" for a in mine)
        parts.append(f"<h2>{esc(q)}</h2><ul>{items}</ul>")
    for a in actors_list:
        page(f"tools/{a['name']}.html", actors.question(a), a["description"][:200], actors.body(a, STORE), ld=actors.faq_ld(a))
    title = f"Public-registry data tools: {len(actors_list)} scrapers for licenses, new businesses, Airbnb and prices"
    lead = (f"<p class='lead'>We maintain <strong>{len(actors_list)} data tools</strong> on the Apify Store that read official registries "
            f"and public sites: contractor licenses in 20 US states, new businesses, Airbnb hosts, property and price data.</p>")
    page("tools.html", title, lead[19:180], f"<h1>{esc(title)}</h1>{lead}{''.join(parts)}")


def build_index() -> None:
    title = "Open business data from public registries: new dental practices, Spanish rural accommodation, contractor licenses"
    body = (f"<h1>{esc(title)}</h1><p class='lead'>Weekly counts and samples taken straight from government registries, "
            f"for people who sell to new businesses.</p><ul>"
            f"<li><a href='{BASE}/dental/'>How many new dental practices opened in the US?</a> By state, from the NPI registry</li>"
            f"<li><a href='{BASE}/es/casas-rurales.html'>¿Cuántas casas rurales hay en España y cuántas tienen web?</a></li>"
            f"<li><a href='{BASE}/tools.html'>All our data tools</a></li></ul>")
    page("index.html", title, "Weekly data from public registries: new US dental practices, Spanish rural accommodation, licenses.", body)


def build_meta() -> None:
    urls = "".join(f"<url><loc>{BASE}/{p.replace('index.html', '')}</loc><lastmod>{TODAY}</lastmod></url>" for p in PAGES)
    (SITE / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding="utf-8")
    # Los buscadores de las IA (GPTBot, PerplexityBot, ClaudeBot) leen robots.txt: se les deja pasar a todo.
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    lines = "\n".join(f"- {BASE}/{p}" for p in PAGES[:60])
    (SITE / "llms.txt").write_text(f"# Open business data\n\nWeekly data from public registries.\n\n{lines}\n", encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    build_dental()
    build_rural()
    build_tools()
    build_index()
    build_meta()
    print(f"{len(PAGES)} paginas en {SITE}")


if __name__ == "__main__":
    main()
