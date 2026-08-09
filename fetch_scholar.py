"""
Fetch Google Scholar publications and citation stats.
Pure stdlib implementation — no external dependencies.
Generates gs_data.json and gs_data_shieldsio.json in google-scholar-stats/.
"""
import urllib.request
import ssl
import re
import html
import json
import os
import sys


SCHOLAR_ID = "if0PW_cAAAAJ"
OUTPUT_DIR = "google-scholar-stats"
URL = f"https://scholar.google.com/citations?hl=en&user={SCHOLAR_ID}&pagesize=100"


def fetch_page() -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    ctx = ssl.create_default_context()
    req = urllib.request.Request(URL, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=45) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse_publications(html_text: str) -> dict:
    """Extract all publication rows from Google Scholar HTML."""
    # Total citations
    m = re.search(r'<td[^>]*class="gsc_rsb_std"[^>]*>(\d+)</td>', html_text)
    total = int(m.group(1)) if m else 0

    rows = re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', html_text, re.DOTALL)
    papers = {}

    for i, row in enumerate(rows):
        # Title + link
        link_m = re.search(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', row, re.DOTALL)
        title = "Untitled"
        link = None
        if link_m:
            title = html.unescape(re.sub(r"<[^>]+>", "", link_m.group(2))).strip()
            href = link_m.group(1)
            if href and not href.startswith("#"):
                link = "https://scholar.google.com" + href

        # Citation count
        cite_m = re.search(r'<a[^>]*class="gsc_a_ac[^>]*>(\d+)</a>', row)
        n_cite = int(cite_m.group(1)) if cite_m else 0

        # Year
        yr_m = re.search(r'<td class="gsc_a_y"><span[^>]*>(\d+)</span>', row)
        year = int(yr_m.group(1)) if yr_m else 0

        # Authors / venue
        fields = re.findall(r'<div class="gs_gray">(.*?)</div>', row, re.DOTALL)
        authors = ""
        venue = ""
        for j, f in enumerate(fields):
            text = html.unescape(re.sub(r"<[^>]+>", "", f)).strip()
            if j == 0:
                authors = text
            elif j == 1:
                venue = text

        pub_id = f"pub_{i}"
        papers[pub_id] = {
            "title": title,
            "url_scholar": link,
            "num_citations": n_cite,
            "year": year,
            "bib": {"title": title, "url": link},
            "authors": authors,
            "venue": venue,
        }

    return {"citedby": total, "publications": papers}


def run():
    print(f"Fetching: {URL}")
    html_text = fetch_page()
    data = parse_publications(html_text)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Main data file
    data_path = os.path.join(OUTPUT_DIR, "gs_data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    n = len(data["publications"])
    print(f"Saved {data_path}  ({n} papers, {data['citedby']} citations)")

    # Shields.io badge data
    shields_path = os.path.join(OUTPUT_DIR, "gs_data_shieldsio.json")
    shields = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(data["citedby"]),
        "color": "9cf",
    }
    with open(shields_path, "w", encoding="utf-8") as f:
        json.dump(shields, f, ensure_ascii=False, indent=2)
    print(f"Saved {shields_path}")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
