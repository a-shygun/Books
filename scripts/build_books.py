#!/usr/bin/env python3
"""Import PDFs, keep a JSON catalog, and render the searchable Pages site."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
IMPORT_DIR = ROOT / "import PDFs"
BOOKS_DIR = ROOT / "Reference Books"
SITE_DIR = ROOT / "site"
CATALOG_PATH = ROOT / "books.json"


def next_index() -> int:
    indexes = [int(match.group(1)) for path in BOOKS_DIR.glob("*.pdf")
               if (match := re.match(r"^(\d+)\s+-\s+", path.name))]
    return max(indexes, default=0) + 1


def import_pdfs() -> None:
    BOOKS_DIR.mkdir(exist_ok=True)
    number = next_index()
    for source in sorted(IMPORT_DIR.glob("*.pdf"), key=lambda p: p.name.casefold()):
        # Remove common download-site suffixes while retaining the actual title.
        title = re.sub(r"\s*\([^)]*(?:z-library|1lib|z-lib)[^)]*\)", "", source.stem, flags=re.I)
        title = re.sub(r"_Low$", "", title).strip()
        destination = BOOKS_DIR / f"{number:03d} - {title}.pdf"
        while destination.exists():
            number += 1
            destination = BOOKS_DIR / f"{number:03d} - {title}.pdf"
        shutil.move(str(source), destination)
        number += 1


def make_catalog() -> list[dict[str, str]]:
    books = []
    for path in sorted(BOOKS_DIR.glob("*.pdf"), key=lambda p: p.name.casefold()):
        title = re.sub(r"^\d+\s+-\s+", "", path.stem)
        books.append({"name": title, "url": "Reference%20Books/" + quote(path.name)})
    CATALOG_PATH.write_text(json.dumps(books, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return books


def make_site(books: list[dict[str, str]]) -> None:
    SITE_DIR.mkdir(exist_ok=True)
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    entries = ",\n".join(
        "      {name: %s, url: %s}" % (json.dumps(book["name"], ensure_ascii=False), json.dumps(book["url"]))
        for book in books
    )
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reference Books</title><style>
body{font:16px/1.5 system-ui,sans-serif;max-width:900px;margin:3rem auto;padding:0 1rem;color:#172033;background:#f7f8fb}
h1{margin-bottom:.25rem}#search{box-sizing:border-box;width:100%;padding:.8rem 1rem;margin:1.5rem 0;border:1px solid #b8c1d1;border-radius:8px;font:inherit}
.book-list{list-style:none;padding:0}.book-list li{padding:.7rem 0;border-bottom:1px solid #dce1e9}.book-list a{color:#174ea6;text-decoration:none}.book-list a:hover{text-decoration:underline}#count{color:#536174}
</style></head><body><h1>Reference Books</h1><p>Browse and search the collection.</p>
<label for="search">Search books</label><input id="search" type="search" placeholder="Type a title or author…" autocomplete="off">
<p id="count" aria-live="polite"></p><ul class="book-list" id="books"></ul>
<script>
const books = [
''' + entries + '''
];
const input=document.querySelector('#search'), list=document.querySelector('#books'), count=document.querySelector('#count');
function render(){const q=input.value.trim().toLocaleLowerCase();const filtered=books.filter(b=>b.name.toLocaleLowerCase().includes(q));
list.replaceChildren(...filtered.map(b=>{const li=document.createElement('li'),a=document.createElement('a');a.href='../'+b.url;a.textContent=b.name;li.append(a);return li}));
count.textContent=`${filtered.length} of ${books.length} books`;}
input.addEventListener('input',render);render();
</script></body></html>
'''
    (SITE_DIR / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    import_pdfs()
    make_site(make_catalog())


if __name__ == "__main__":
    main()
