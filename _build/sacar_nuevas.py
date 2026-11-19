"""Clinicas dentales recien dadas de alta en el registro NPI (CMS), desde los ficheros semanales.
Uso: python -I -X utf8 sacar_nuevas.py <npidata_semana1.csv> [<semana2.csv> ...]
Sale clinicas_nuevas.csv. Solo organizaciones (tipo 2) con codigo de dentista (1223...) y alta desde MIN_DATE:
el fichero semanal trae tambien cambios de fichas viejas, que no son clinicas nuevas."""
import csv
import os
import sys
from datetime import date, datetime, timedelta

# En GitHub Actions se pasa MIN_DAYS (ventana movil); sin ella, la fecha fija de la primera campana.
MIN_DATE = date.today() - timedelta(days=int(os.environ["MIN_DAYS"])) if os.environ.get("MIN_DAYS") else date(2026, 10, 15)
P = "Provider Business Practice Location Address "


def is_new_dental(x: dict) -> bool:
    taxes = [x.get(f"Healthcare Provider Taxonomy Code_{i}", "") for i in range(1, 16)]
    if x["Entity Type Code"] != "2" or not any(t.startswith("1223") for t in taxes):
        return False
    return datetime.strptime(x["Provider Enumeration Date"], "%m/%d/%Y").date() >= MIN_DATE


def row(x: dict) -> dict:
    tel = x[P + "Telephone Number"]
    return {"npi": x["NPI"], "registered": datetime.strptime(x["Provider Enumeration Date"], "%m/%d/%Y").date().isoformat(),
            "practice": x["Provider Organization Name (Legal Business Name)"].title(),
            "owner": f"{x['Authorized Official First Name']} {x['Authorized Official Last Name']}".title().strip(),
            "owner_title": x["Authorized Official Title or Position"].title(),
            "phone": f"({tel[:3]}) {tel[3:6]}-{tel[6:]}" if len(tel) == 10 else tel,
            "address": x["Provider First Line Business Practice Location Address"].title(), "city": x[P + "City Name"].title(), "state": x[P + "State Name"],
            "zip": x[P + "Postal Code"][:5]}


def main() -> None:
    seen = {}
    for path in sys.argv[1:]:
        for x in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
            if is_new_dental(x):
                seen[x["NPI"]] = row(x)
    rows = sorted(seen.values(), key=lambda r: (r["state"], r["registered"]), reverse=False)
    with open(os.environ.get("CLINICS_CSV", "clinicas_nuevas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"clinicas nuevas {len(rows)} | con telefono {sum(1 for r in rows if r['phone'])} | "
          f"con responsable {sum(1 for r in rows if r['owner'])}")


if __name__ == "__main__":
    main()
