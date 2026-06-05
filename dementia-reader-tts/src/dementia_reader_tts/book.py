"""Load a book from a directory of chapter text files.

Layout:
    my-book/
        book.toml            # optional metadata + explicit chapter order
        chapter-01.txt
        chapter-02.txt

If ``book.toml`` is absent, chapters are the ``*.txt`` files in sorted order and
the book id is the directory name.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chapter:
    id: str
    title: str
    text: str


@dataclass
class Book:
    id: str
    title: str
    chapters: list[Chapter] = field(default_factory=list)


def load_book(path: str | Path) -> Book:
    path = Path(path)
    if not path.is_dir():
        raise NotADirectoryError(f"Book path is not a directory: {path}")

    meta_path = path / "book.toml"
    meta: dict = {}
    if meta_path.exists():
        with meta_path.open("rb") as fh:
            meta = tomllib.load(fh)

    book_id = meta.get("id", path.name)
    title = meta.get("title", book_id)

    chapter_files: list[Path]
    if "chapters" in meta:
        chapter_files = [path / name for name in meta["chapters"]]
    else:
        chapter_files = sorted(path.glob("*.txt"))

    chapters: list[Chapter] = []
    for cf in chapter_files:
        if not cf.exists():
            raise FileNotFoundError(f"Chapter file listed but not found: {cf}")
        text = cf.read_text(encoding="utf-8").strip()
        if not text:
            continue
        first_line = text.splitlines()[0].strip()
        chapters.append(Chapter(id=cf.stem, title=first_line[:80] or cf.stem, text=text))

    if not chapters:
        raise ValueError(f"No non-empty chapter .txt files found in {path}")
    return Book(id=book_id, title=title, chapters=chapters)
