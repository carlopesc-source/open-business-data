"""Baja los dos ultimos ficheros semanales de NPPES (CMS) y deja sus CSV en la carpeta que se le pase.
Uso: python -I -X utf8 bajar_nppes.py <carpeta>"""
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://download.cms.gov/nppes/"
UA = {"User-Agent": "Mozilla/5.0"}


def get(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    page = get(BASE + "NPI_Files.html").decode("utf-8", "replace")
    zips = sorted(set(re.findall(r"NPPES_Data_Dissemination_\d{6}_\d{6}_Weekly_V2\.zip", page)))
    if not zips:
        sys.exit("NPPES: no aparece ningun fichero semanal en NPI_Files.html")
    for name in zips[-2:]:
        path = out / name
        path.write_bytes(get(BASE + name))
        with zipfile.ZipFile(path) as z:
            # El zip trae tambien el fichero de cabeceras y otros (othername, pl): solo interesa npidata_pfile.
            for member in z.namelist():
                if member.startswith("npidata_pfile") and "fileheader" not in member:
                    z.extract(member, out)
        print(f"{name}: {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
