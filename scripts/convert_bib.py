import re
import yaml
from pathlib import Path


BIB_FILE = Path("_bibliography/papers.bib")
OUTPUT_FILE = Path("_data/publications.yml")


def parse_bibtex(text):
    entries = []

    # Find @type{key, ...} blocks
    pattern = re.compile(
        r"@(\w+)\s*\{\s*([^,]+),\s*(.*?)\n\}",
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(text):
        entry_type = match.group(1).lower()
        key = match.group(2).strip()
        body = match.group(3)

        fields = {}

        # Match field = {value}, field = "value", or field = value
        field_pattern = re.compile(
            r'(\w+)\s*=\s*(?:\{((?:[^{}]|\{[^{}]*\})*)\}|"([^"]*)"|([^,\n]+))',
            re.DOTALL
        )

        for field_match in field_pattern.finditer(body):
            name = field_match.group(1).lower()
            value = (
                field_match.group(2)
                or field_match.group(3)
                or field_match.group(4)
                or ""
            ).strip()

            fields[name] = value

        entries.append({
            "entry_type": entry_type,
            "key": key,
            "fields": fields,
        })

    return entries


def clean_latex(value):
    if not value:
        return value

    replacements = {
        r'\"{a}': "ä",
        r'\"{o}': "ö",
        r'\"{u}': "ü",
        r'\"{A}': "Ä",
        r'\"{O}': "Ö",
        r'\"{U}': "Ü",
        r"\'{e}": "é",
        r"\'{E}": "É",
        r"\&": "&",
        r"\{": "",
        r"\}": "",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value


def publication_type(entry):
    entry_type = entry["entry_type"]
    fields = entry["fields"]

    if fields.get("archiveprefix", "").lower() == "arxiv":
        return "preprint"

    if fields.get("eprint"):
        return "preprint"

    if entry_type == "article":
        return "article"

    if entry_type == "book":
        return "book"

    if entry_type in ("incollection", "inbook"):
        return "chapter"

    if entry_type in ("phdthesis", "mastersthesis", "thesis"):
        return "thesis"

    return "other"


def parse_authors(author_string):
    authors = []

    for author in re.split(r"\s+and\s+", author_string):
        author = author.strip()

        if "," in author:
            last, first = author.split(",", 1)
            name = f"{first.strip()} {last.strip()}"
        else:
            name = author

        authors.append(clean_latex(name))

    return authors


def convert(entry):
    fields = entry["fields"]

    publication = {
        "key": entry["key"],
        "type": publication_type(entry),
        "year": int(fields.get("year", 0)),
        "title": clean_latex(fields.get("title", "")),
        "authors": parse_authors(fields.get("author", "")),
    }

    optional_fields = [
        "journal",
        "booktitle",
        "publisher",
        "volume",
        "number",
        "pages",
        "doi",
        "url",
        "abstract",
        "eprint",
        "school",
        "isbn",
    ]

    for field in optional_fields:
        if fields.get(field):
            publication[field] = clean_latex(fields[field])

    if fields.get("eprint"):
        publication["arxiv"] = fields["eprint"]

    return publication


def main():
    if not BIB_FILE.exists():
        raise FileNotFoundError(f"Could not find {BIB_FILE}")

    text = BIB_FILE.read_text(encoding="utf-8")

    entries = parse_bibtex(text)

    publications = [convert(entry) for entry in entries]

    publications.sort(
        key=lambda publication: publication["year"],
        reverse=True
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            publications,
            file,
            allow_unicode=True,
            sort_keys=False,
            width=120
        )

    print(f"Converted {len(publications)} publications.")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
