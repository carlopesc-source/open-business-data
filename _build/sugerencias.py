"""Busquedas reales de Google (autocompletado) para cada actor: es lo que la gente escribe de verdad.
Se corre a mano de vez en cuando (no en GitHub Actions, para no pedirle a Google cada semana).
Uso: python -I -X utf8 _build/sugerencias.py  -> _build/datos/suggest.json"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import actors  # noqa: E402

URL = "https://suggestqueries.google.com/complete/search?client=firefox&hl=en&q="
# Ruido: frases que no describen lo que hace ningun actor (paises que no cubre, extensiones, quejas).
NOISE = ("india", "canada", "australia", "uk ", " uk", "not working", "extension", "app", "reddit", "login", "jobs near", "github", "ampifire", "keepa", "camelcamel")


def suggest(q: str) -> list:
    raw = urllib.request.urlopen(URL + urllib.parse.quote(q), timeout=20).read().decode("utf-8", "replace")
    return json.loads(raw)[1]


# Semillas cortas: Google solo autocompleta frases de 2-4 palabras; una pregunta larga no devuelve nada.
SEEDS = {
    "airbnb-host-portfolio": ["airbnb host list", "airbnb hosts with multiple", "find airbnb host"],
    "airbnb-new-listings": ["new airbnb listings", "airbnb price drop", "airbnb listings data"],
    "airbnb-reviews": ["airbnb reviews scraper", "download airbnb reviews", "airbnb reviews data"],
    "airbnb-license-check": ["airbnb license check", "short term rental license lookup", "str license lookup"],
    "australia-visa-sponsorship-jobs": ["visa sponsorship jobs australia", "482 visa sponsor jobs", "working holiday jobs australia"],
    "google-ads-text": ["google ads transparency", "see competitor google ads", "google ads library"],
    "google-maps-contractor-license-check": ["check contractor license", "google maps contractors", "verify contractor license"],
    "uk-company-owners": ["companies house director search", "uk company owner search", "psc register search"],
    "uk-hiring-companies": ["uk companies hiring", "companies hiring uk", "who is hiring uk"],
    "uk-new-companies": ["new companies house registrations", "new uk companies list", "companies house new incorporations"],
    "uk-food-business-leads": ["new food business uk", "food hygiene rating data", "fsa food hygiene api"],
    "amazon-real-deals": ["is this amazon deal good", "amazon fake deals", "amazon deal checker"],
    "rightmove-listings": ["rightmove scraper", "rightmove price reduced", "rightmove sold prices"],
    "us-company-check": ["kyb verification", "llc lookup by state", "new llc filings"],
    "google-play-reviews": ["google play reviews scraper", "download google play reviews", "google play reviews export"],
    "kalshi-trades-api": ["kalshi api", "kalshi trade history", "kalshi whale"],
    "us-active-contractors": ["contractor leads", "list of contractors", "active contractor license"],
    "zillow-motivated-sellers": ["motivated sellers", "zillow motivated seller", "motivated seller leads"],
    "spain-rural-accommodation-registry": ["casas rurales", "rural houses spain", "registro turismo rural"],
    "us-storm-roofing-leads": ["roofing leads", "hail storm leads", "storm damage leads"],
    "us-new-business-openings": ["new business leads", "new business openings", "new business list"],
    "connecticut-contractor-license-lookup": ["ct contractor license lookup", "connecticut contractor license", "ct license lookup"],
}


def seeds(actor: dict) -> list:
    if actor["name"] in SEEDS:
        return SEEDS[actor["name"]]
    q = actors.question(actor).lower().replace("how do i ", "").rstrip("?")
    title = actor["title"].split(":")[0].split(" - ")[0].lower()
    return [q, title, "how to " + q]


def main() -> None:
    store = json.load(open(ROOT / "datos" / "store.json", encoding="utf-8"))["data"]["items"]
    out = {}
    for a in store:
        found = []
        for s in seeds(a):
            for x in suggest(s):
                if x not in found and not any(n in f" {x} " for n in NOISE):
                    found.append(x)
            time.sleep(0.4)
        out[a["name"]] = found[:15]
        print(a["name"], len(found))
    (ROOT / "datos" / "suggest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
