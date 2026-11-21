"""Paginas sonda de nichos (22-11-2026): una por tema candidato, con cifras leidas en directo del registro oficial.
Si en 3-4 semanas Search Console les da impresiones, el tema tiene demanda y se construye actor o lista.
Lo importa build.py; cada pagina falla sola sin tumbar las demas."""
import csv
import html
import io
import json
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta

TX = "https://data.texas.gov/resource"
CANARIAS_VV = ("https://datos.canarias.es/catalogos/general/dataset/9f4355a2-d086-4384-ba72-d8c99aa2d544"
               "/resource/8ff8cc43-c00b-4513-8f42-a5b961c579e1/download/establecimientos")


def _get(url: str, timeout: int = 120) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "open-business-data"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _soql(dataset: str, query: str) -> list:
    return json.loads(_get(f"{TX}/{dataset}.json?" + urllib.parse.urlencode({"$query": query})))


def _n(x) -> str:
    return f"{int(x):,}"


def _faq_ld(pairs: list) -> dict:
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}


def texas_liquor(page, base: str) -> None:
    since = (date.today() - timedelta(days=30)).isoformat() + "T00:00:00"
    active = _soql("7hf9-qc9f", "SELECT count(*) AS n WHERE license_status='Active'")[0]["n"]
    new = _soql("7hf9-qc9f", f"SELECT count(*) AS n WHERE original_issue_date >= '{since}'")[0]["n"]
    pending = _soql("mxm5-tdpj", f"SELECT count(*) AS n WHERE submission_date >= '{since}'")[0]["n"]
    cities = _soql("mxm5-tdpj", f"SELECT city, count(*) AS n WHERE submission_date >= '{since}' GROUP BY city ORDER BY n DESC LIMIT 8")
    q = "How many new liquor licenses are issued in Texas each month?"
    first = (f"{_n(new)} new Texas liquor licenses were issued in the last 30 days, and {_n(pending)} new applications were filed, "
             f"out of {_n(active)} active TABC licenses.")
    rows = "".join(f"<tr><td>{html.escape(c['city'])}</td><td>{_n(c['n'])}</td></tr>" for c in cities)
    faq = [(q, first),
           ("Where does the data come from?", "From the Texas Alcoholic Beverage Commission (TABC) open data on data.texas.gov: the license register and the pending new applications."),
           ("Who uses new liquor license data?", "Beverage distributors, POS and payment providers, insurers and suppliers: a bar or restaurant that just applied is choosing all of them.")]
    body = (f"<h1>{q}</h1><p class='lead'>{first}</p><h2>New applications in the last 30 days, by city</h2>"
            f"<table><tr><th>City</th><th>Applications</th></tr>{rows}</table>"
            + "".join(f"<h3>{html.escape(a)}</h3><p>{html.escape(b)}</p>" for a, b in faq[1:]))
    page("niches/texas-new-liquor-licenses.html", q + f" {_n(new)} in 30 days", first, body, ld=_faq_ld(faq))


def texas_cosmetology(page, base: str) -> None:
    rows = _soql("7358-krk7", "SELECT license_type, count(*) AS n WHERE license_type like '%Cosmetolog%' OR license_type like '%Barber%' "
                               "OR license_type like '%Esthetic%' OR license_type like '%Manicur%' GROUP BY license_type ORDER BY n DESC LIMIT 12")
    total = sum(int(r["n"]) for r in rows)
    shops = sum(int(r["n"]) for r in rows if "Establishment" in r["license_type"] or "School" in r["license_type"])
    q = "How many licensed cosmetologists and salons are there in Texas?"
    first = (f"Texas has {_n(total)} current cosmetology, barber, esthetician and manicurist licenses, "
             f"{_n(shops)} of them for establishments and schools, according to the TDLR register.")
    table = "".join(f"<tr><td>{html.escape(r['license_type'])}</td><td>{_n(r['n'])}</td></tr>" for r in rows)
    faq = [(q, first),
           ("How do I look up a cosmetology license in Texas?", "The Texas Department of Licensing and Regulation (TDLR) publishes every license with its number, type and expiry date on data.texas.gov."),
           ("Who uses cosmetology license data?", "Beauty supply distributors, salon software, booking apps, insurers and schools looking for new licensees.")]
    body = (f"<h1>{q}</h1><p class='lead'>{first}</p><table><tr><th>License type</th><th>Licenses</th></tr>{table}</table>"
            + "".join(f"<h3>{html.escape(a)}</h3><p>{html.escape(b)}</p>" for a, b in faq[1:]))
    page("niches/texas-cosmetology-licenses.html", q + f" {_n(total)} licenses", first, body, ld=_faq_ld(faq))


def canarias_vv(page, base: str) -> None:
    data = list(csv.DictReader(io.StringIO(_get(CANARIAS_VV, timeout=300)), delimiter=";"))
    islands = Counter((r.get("direccion_isla_nombre") or "").strip() for r in data).most_common()
    towns = Counter((r.get("direccion_municipio_nombre") or "").strip() for r in data).most_common(10)
    beds = sum(int(r["plazas"]) for r in data if (r.get("plazas") or "").strip().isdigit())
    q = "¿Cuántas viviendas vacacionales hay registradas en Canarias?"
    first = (f"Canarias tiene {_n(len(data)).replace(',', '.')} viviendas vacacionales en el registro oficial del Gobierno de Canarias, "
             f"con {_n(beds).replace(',', '.')} plazas.")
    t1 = "".join(f"<tr><td>{html.escape(i)}</td><td>{_n(n).replace(',', '.')}</td></tr>" for i, n in islands)
    t2 = "".join(f"<tr><td>{html.escape(m)}</td><td>{_n(n).replace(',', '.')}</td></tr>" for m, n in towns)
    faq = [(q, first),
           ("¿De dónde salen los datos?", "Del registro de establecimientos turísticos que publica el Gobierno de Canarias en datos.canarias.es."),
           ("¿Quién usa este registro?", "Gestoras de alquiler vacacional, limpieza, fotógrafos, seguros y programas de reservas: cada vivienda registrada es un cliente posible.")]
    body = (f"<h1>{q}</h1><p class='lead'>{first}</p><h2>Por isla</h2><table><tr><th>Isla</th><th>Viviendas</th></tr>{t1}</table>"
            f"<h2>Los 10 municipios con más</h2><table><tr><th>Municipio</th><th>Viviendas</th></tr>{t2}</table>"
            + "".join(f"<h3>{html.escape(a)}</h3><p>{html.escape(b)}</p>" for a, b in faq[1:]))
    page("es/viviendas-vacacionales-canarias.html", q + f" {_n(len(data)).replace(',', '.')}", first, body, lang="es", ld=_faq_ld(faq))


def build_niches(page, base: str) -> list:
    done = []
    for fn in (texas_liquor, texas_cosmetology, canarias_vv):
        try:
            fn(page, base)
            done.append(fn.__name__)
        except Exception as e:  # una fuente caida no tumba las demas paginas
            print(f"nicho {fn.__name__} fallo: {e}")
    return done
