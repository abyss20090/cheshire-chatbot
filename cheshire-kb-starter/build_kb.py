import os, re, io, time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

INFILE = "urls.txt"
OUTDIR = Path("dist")
OUTDIR.mkdir(exist_ok=True, parents=True)

ROUTES = [
    (("admission", "apply", "inquire", "tuition-financial-aid"), "admissions.txt"),
    (("academic", "academics", "curriculum", "college-counseling", "international-baccalaureate"), "academics.txt"),
    (("athletic", "team-pages", "/team/"), "athletics.txt"),
    (("campus-life", "boarding-at-ca", "day-student-life", "student-health-support", "dei", "clubs", "community-weekends", "international-student-life", "sustainability"), "campus_life.txt"),
    (("calendar", "major-dates", "schedule", "year-at-a-glance"), "calendars.txt"),
    (("about", "commencement", "employment", "facility-rentals", "faculty-staff-directory", "head-of-school"), "about.txt"),
    (("school-news", "/2024/", "/2025/"), "news.txt"),
]

DEFAULT_FILE = "misc.txt"
HEADERS = {"User-Agent":"Mozilla/5.0 (KB bot; +https://github.com/)"}

def which_outfile(url: str) -> str:
    path = urlparse(url).path.lower()
    for keys, fname in ROUTES:
        if any(k in path for k in keys):
            return fname
    return DEFAULT_FILE

def is_pdf_url(url: str) -> bool:
    return urlparse(url).path.lower().endswith(".pdf")

def fetch(url: str) -> bytes:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content

def clean_text(t: str) -> str:
    t = re.sub(r"\r\n", "\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def html_to_text(html: bytes, base_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript","form","nav","footer","header","aside"]):
        tag.decompose()
    parts = []
    title = soup.title.get_text(strip=True) if soup.title else ""
    if title: parts.append(f"# {title}")
    for h in soup.find_all(re.compile(r"^h[1-4]$")):
        txt = h.get_text(" ", strip=True)
        if txt: parts.append(f"## {txt}")
    for li in soup.find_all("li"):
        txt = li.get_text(" ", strip=True)
        if txt: parts.append(f"- {txt}")
    for p in soup.find_all("p"):
        txt = p.get_text(" ", strip=True)
        if txt: parts.append(txt)
    text = clean_text("\n".join(parts))
    if not text: text = "(No extractable text)"
    return f"=== SOURCE: {base_url} ===\n{text}\n"

def pdf_to_text(pdf_bytes: bytes, base_url: str) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    text = clean_text("\n".join(pages))
    return f"=== SOURCE: {base_url} ===\n{text}\n"

def write_append(fname: str, text: str):
    (OUTDIR / fname).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTDIR / fname, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")

def main():
    for p in OUTDIR.glob("*.txt"):
        p.unlink()

    with open(INFILE, "r", encoding="utf-8") as f:
        urls = [u.strip() for u in f if u.strip() and not u.strip().startswith("#")]

    for url in urls:
        try:
            if is_pdf_url(url):
                b = fetch(url)
                text = pdf_to_text(b, url)
            else:
                b = fetch(url)
                text = html_to_text(b, url)
            outfile = which_outfile(url)
            write_append(outfile, text)
            print("OK:", url, "->", outfile)
            time.sleep(0.5)
        except Exception as e:
            write_append("errors.txt", f"{url}\nERROR: {e}")
            print("ERR:", url, e)

    big = []
    for p in sorted(OUTDIR.glob("*.txt")):
        if p.name == "school_faq.txt":
            continue
        big.append("\n" + "="*80 + f"\nFILE: {p.name}\n" + "="*80 + "\n")
        big.append(p.read_text(encoding="utf-8"))
    (OUTDIR/"school_faq.txt").write_text("".join(big), encoding="utf-8")
    print("Wrote:", OUTDIR/"school_faq.txt")

if __name__ == "__main__":
    main()
