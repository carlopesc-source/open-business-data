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
    return (f"<h1>{esc(q)}</h1><p class='lead'>Use <a href='{esc(actor['url'])}'><strong>{esc(actor['title'])}</strong></a> "
            f"on the Apify Store. {esc(actor['description'])}</p>{price_html}"
            f"<div class='cta'>Run it from the browser, no code needed: <a href='{esc(actor['url'])}'>{esc(actor['url'])}</a>. "
            f"More tools from the same publisher: <a href='{store}'>{store}</a>.</div>")
