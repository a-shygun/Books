#!/usr/bin/env python3
"""Import PDFs and regenerate the searchable GitHub-hosted book catalog."""

import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
IMPORT_DIR = ROOT / "import PDFs"
BOOKS_DIR = ROOT / "Reference Books"
CATALOG_PATH = ROOT / "books.json"
PAGE_PATH = ROOT / "index.html"
REPOSITORY = "a-shygun/Books"
BRANCH = "main"


def next_index() -> int:
    indexes = []
    for path in BOOKS_DIR.glob("*.pdf"):
        match = re.match(r"^(\d+)\s+-\s+", path.name)
        if match:
            indexes.append(int(match.group(1)))
    return max(indexes, default=0) + 1


def import_pdfs() -> int:
    """Move queued PDFs into Reference Books with the next available indexes."""
    number = next_index()
    moved = 0
    for source in sorted(IMPORT_DIR.glob("*.pdf"), key=lambda item: item.name.casefold()):
        title = re.sub(r"\s*\([^)]*(?:z-library|1lib|z-lib)[^)]*\)", "", source.stem, flags=re.I)
        title = re.sub(r"_Low$", "", title).strip()
        destination = BOOKS_DIR / f"{number:03d} - {title}.pdf"
        while destination.exists():
            number += 1
            destination = BOOKS_DIR / f"{number:03d} - {title}.pdf"
        shutil.move(str(source), destination)
        moved += 1
        number += 1
    return moved


def build_catalog() -> list[dict[str, str]]:
    books = []
    for path in sorted(BOOKS_DIR.glob("*.pdf"), key=lambda item: item.name.casefold()):
        name = re.sub(r"^\d+\s+-\s+", "", path.stem)
        encoded_path = "/".join(quote(part, safe="") for part in ("Reference Books", path.name))
        url = f"https://github.com/{REPOSITORY}/blob/{BRANCH}/{encoded_path}"
        books.append({"name": name, "url": url})
    CATALOG_PATH.write_text(json.dumps(books, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return books


def build_page() -> None:
    page = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reference Books</title>
  <style>
    body{font:16px/1.5 system-ui,sans-serif;max-width:900px;margin:3rem auto;padding:0 1rem;color:#172033;background:#f7f8fb}
    h1{margin-bottom:.25rem}#search{box-sizing:border-box;width:100%;padding:.8rem 1rem;margin:1.5rem 0;border:1px solid #b8c1d1;border-radius:8px;font:inherit}
    .book-list{list-style:none;padding:0}.book-list li{padding:.7rem 0;border-bottom:1px solid #dce1e9}.book-list a{color:#174ea6;text-decoration:none}.book-list a:hover{text-decoration:underline}#count{color:#536174}
  </style>
</head>
<body>
  <h1>Reference Books</h1>
  <p>Browse and search the collection. Book links open their files on GitHub.</p>
  <label for="search">Search books</label>
  <input id="search" type="search" placeholder="Type a title or author…" autocomplete="off">
  <p id="count" aria-live="polite"></p>
  <ul class="book-list" id="books"></ul>
  <script>
    fetch('./books.json').then(response => {
      if (!response.ok) throw new Error('Could not load the book catalog');
      return response.json();
    }).then(books => {
      const input = document.querySelector('#search');
      const list = document.querySelector('#books');
      const count = document.querySelector('#count');
      function render() {
        const query = input.value.trim().toLocaleLowerCase();
        const filtered = books.filter(book => book.name.toLocaleLowerCase().includes(query));
        list.replaceChildren(...filtered.map(book => {
          const item = document.createElement('li');
          const link = document.createElement('a');
          link.href = book.url;
          link.textContent = book.name;
          item.append(link);
          return item;
        }));
        count.textContent = `${filtered.length} of ${books.length} books`;
      }
      input.addEventListener('input', render);
      render();
    }).catch(error => {
      document.querySelector('#count').textContent = error.message;
    });
  </script>
</body>
</html>
'''
    PAGE_PATH.write_text(page, encoding="utf-8")


def main() -> None:
    moved = import_pdfs()
    books = build_catalog()
    build_page()
    print(f"Moved {moved} PDF(s); wrote books.json and index.html for {len(books)} books.")


if __name__ == "__main__":
    main()
