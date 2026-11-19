"""Una pagina por actor de la tienda: el titulo es la pregunta que haria la gente a ChatGPT y la primera frase la contesta.
Lo importa build.py; los datos salen de datos/store.json (API publica de la tienda de Apify)."""
import html

# Las preguntas se escriben a mano: un titulo automatico ("How do I get X Scraper?") no es lo que nadie pregunta.
QUESTIONS = {
    "airbnb-host-portfolio": "How do I find Airbnb hosts who manage several listings in a city?",
    "airbnb-new-listings": "How do I track new Airbnb listings and price drops in a city?",
    "airbnb-reviews": "How do I download all reviews of Airbnb listings in a city?",
    "airbnb-license-check": "How do I check if an Airbnb listing has a valid short-term rental license?",
    "amazon-price-history": "How do I see the price history of an Amazon product without Keepa?",
    "amazon-price-drops": "How do I track Amazon price drops and Best Sellers Rank in bulk?",
    "amazon-real-deals": "How do I know if an Amazon deal is really a good price?",
    "australia-visa-sponsorship-jobs": "Where can I find Australian jobs that offer visa sponsorship?",
    "us-contractor-license-lookup": "How do I verify contractor licenses in bulk across US states?",
    "google-ads-text": "How do I see the text of a competitor's Google Ads?",
    "google-maps-contractor-license-check": "How do I check if contractors on Google Maps have a valid license?",
    "uk-company-owners": "How do I find people in the UK who own several companies?",
    "uk-hiring-companies": "How do I find UK companies that are hiring right now?",
    "uk-new-companies": "How do I get a daily list of new UK companies from Companies House?",
    "uk-food-business-leads": "How do I find new food businesses opening in the UK?",
    "rightmove-listings": "How do I scrape Rightmove price drops with Land Registry sold prices?",
    "redfin-listings": "How do I scrape Redfin homes for sale and price drops?",
    "zillow-motivated-sellers": "How do I find motivated sellers on Zillow?",
    "us-company-check": "How do I verify a US company (KYB) and find new LLC filings by state?",
    "google-play-reviews": "How do I download Google Play reviews with developer replies?",
    "youtube-outliers": "How do I find YouTube videos that beat their channel's average views?",
    "kalshi-trades-api": "How do I get Kalshi trade history and whale trades?",
    "us-active-contractors": "How do I find active US contractors with a phone number and a valid license?",
    "us-building-permits": "How do I get new building permits as contractor leads?",
    "spain-rural-accommodation-registry": "How do I get a list of rural houses in Spain with phone and email?",
    "us-storm-roofing-leads": "How do I find roofing leads after a hail storm?",
    "us-new-business-openings": "How do I find new business openings in the US with a phone number?",
}


def question(actor: dict) -> str:
    name = actor["name"]
    if name in QUESTIONS:
        return QUESTIONS[name]
    if name.endswith("-contractor-license-lookup"):
        state = actor["title"].split(" Contractor")[0]
        article = "an" if state[0] in "AEIOU" else "a"
        return f"How do I verify {article} {state} contractor license?"
    return f"What does {actor['title']} do?"


def prices(actor: dict) -> list:
    # Precio del plan FREE de cada evento: es lo que paga un comprador nuevo. El evento de arranque no se ensena.
    events = ((actor.get("currentPricingInfo") or {}).get("pricingPerEvent") or {}).get("actorChargeEvents") or {}
    out = []
    for key, ev in events.items():
        if key == "apify-actor-start":
            continue
        tiers = ev.get("eventTieredPricingUsd") or {}
        usd = (tiers.get("FREE") or {}).get("tieredEventPriceUsd", ev.get("eventPriceUsd"))
        if usd is not None:
            title = ev.get("eventTitle") or key
            # Algunos eventos llevan de titulo el nombre entero del actor: ahi se dice "result".
            out.append((title if len(title) <= 40 else "result", usd))
    return out


def body(actor: dict, store: str) -> str:
    esc = html.escape
    q = question(actor)
    price = prices(actor)
    price_html = ("<h2>How much does it cost?</h2><ul>" + "".join(
        f"<li><strong>${usd:g}</strong> per {esc(title)}</li>" for title, usd in price) + "</ul>") if price else ""
    searches = also(actor)
    also_html = ("<h2>Also answers these searches</h2><ul>" + "".join(f"<li>{esc(s)}</li>" for s in searches) + "</ul>") if searches else ""
    faq_html = "<h2>FAQ</h2>" + "".join(f"<h3>{esc(fq)}</h3><p>{esc(fa)}</p>" for fq, fa in faq(actor))
    return (f"<h1>{esc(q)}</h1><p class='lead'>Use <a href='{esc(actor['url'])}'><strong>{esc(actor['title'])}</strong></a> "
            f"on the Apify Store. {esc(actor['description'])}</p>{price_html}"
            f"<div class='cta'>Run it from the browser, no code needed: <a href='{esc(actor['url'])}'>{esc(actor['url'])}</a>. "
            f"More tools from the same publisher: <a href='{store}'>{store}</a>.</div>{also_html}{faq_html}")


def faq_ld(actor: dict) -> dict:
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq(actor)]}


# Otras formas reales de buscar lo mismo, escogidas a mano del autocompletado de Google (datos/suggest.json, 19-11).
# Solo las que el actor contesta de verdad: el autocompletado trae mucha basura ("airbnb host shopping list").
ALSO = {
    "airbnb-host-portfolio": ["airbnb hosts with multiple listings", "airbnb host list by city", "airbnb host directory", "airbnb hosting multiple properties", "find airbnb property managers"],
    "airbnb-new-listings": ["new airbnb listings in my city", "airbnb price drop alert", "airbnb listings data by city", "track airbnb prices"],
    "airbnb-reviews": ["airbnb reviews scraper", "download airbnb reviews", "export airbnb reviews to csv", "airbnb reviews data"],
    "airbnb-license-check": ["airbnb license check", "short term rental license lookup", "str license lookup", "does this airbnb have a permit"],
    "amazon-price-history": ["amazon price history", "amazon price history checker", "amazon price history tracker", "lowest price ever on amazon"],
    "amazon-price-drops": ["amazon price drop tracker", "amazon price tracker in bulk", "amazon best sellers rank tracker", "amazon price alerts"],
    "amazon-real-deals": ["is this amazon deal good", "amazon fake deals", "amazon deal checker", "was this price really lower on amazon"],
    "australia-visa-sponsorship-jobs": ["visa sponsorship jobs australia", "482 visa sponsor jobs", "working holiday jobs australia", "employers that sponsor visas in australia"],
    "us-contractor-license-lookup": ["how to check contractor license", "contractor license lookup by state", "verify contractor license online", "check contractor license status", "bulk contractor license verification"],
    "google-ads-text": ["google ads transparency center", "see competitor google ads", "google ads library", "competitor ad copy"],
    "google-maps-contractor-license-check": ["check contractor license from google maps", "are google maps contractors licensed", "verify roofer license", "verify contractor license"],
    "uk-company-owners": ["companies house director search", "companies house director search by name", "psc register search", "find all companies owned by a person uk"],
    "uk-hiring-companies": ["uk companies hiring now", "companies hiring in the uk", "who is hiring uk", "linkedin jobs uk companies"],
    "uk-new-companies": ["new companies house registrations", "new uk companies list", "companies house new incorporations", "daily new companies uk"],
    "uk-food-business-leads": ["new food business uk", "food hygiene rating data", "fsa food hygiene api", "new restaurants opening uk"],
    "rightmove-listings": ["rightmove scraper", "rightmove price reduced", "rightmove sold prices", "land registry sold prices"],
    "redfin-listings": ["redfin scraper", "redfin price drops", "redfin homes for sale data", "redfin comps"],
    "zillow-motivated-sellers": ["motivated seller leads", "zillow motivated sellers", "find motivated sellers", "zillow price cut list"],
    "us-company-check": ["kyb verification", "llc lookup by state", "new llc filings", "verify a us company"],
    "google-play-reviews": ["google play reviews scraper", "download google play reviews", "google play reviews export", "google play developer replies"],
    "app-store-reviews": ["app store reviews scraper", "download app store reviews", "app store reviews all countries"],
    "youtube-outliers": ["youtube outlier finder", "youtube outlier search", "youtube video outlier finder", "find viral youtube videos in a niche"],
    "kalshi-trades-api": ["kalshi trade history", "kalshi api trade history", "kalshi historical trade data", "kalshi historical trades", "kalshi transaction history"],
    "us-active-contractors": ["contractor leads", "list of licensed contractors", "active contractor license list", "contractor phone numbers"],
    "us-building-permits": ["building permit data", "new building permits list", "building permits contractor leads", "permit leads for contractors"],
    "spain-rural-accommodation-registry": ["casas rurales España", "rural houses spain list", "registro de turismo rural", "listado casas rurales con teléfono"],
    "us-storm-roofing-leads": ["roofing leads", "hail storm leads", "storm damage leads", "hail reports by zip"],
    "us-new-business-openings": ["new business leads", "new business openings", "new business list with phone", "newly registered businesses"],
}


def also(actor: dict) -> list:
    if actor["name"] in ALSO:
        return ALSO[actor["name"]]
    if actor["name"].endswith("-contractor-license-lookup"):
        s = actor["title"].split(" Contractor")[0]
        return [f"verify {s} contractor license", f"how to check a contractor license in {s}", f"{s} contractor license lookup",
                f"{s} contractor license search", f"check {s} contractor license status", f"is my contractor licensed in {s}"]
    return []


def faq(actor: dict) -> list:
    # Preguntas con respuesta cierta para todos: precio, si hace falta programar y como se usa.
    p = prices(actor)
    cost = ("It is pay per result: " + ", ".join(f"${usd:g} per {t}" for t, usd in p) + ". You pay only for rows delivered."
            if p else "See the current price on its Apify Store page.")
    return [(f"How much does {actor['title']} cost?", cost),
            ("Do I need to write code?", "No. You fill in a form on the Apify Store page and press Start; results download as CSV, Excel or JSON."),
            ("Can I connect it to my own tools?", "Yes. Every run is also available through the Apify API, and can feed Zapier, Make, n8n or Google Sheets.")]
