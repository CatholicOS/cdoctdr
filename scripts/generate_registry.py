#!/usr/bin/env python3
"""Validate data/doctors.json and render registry/doctors.md.

The JSON is the source of truth; this script is the only writer of the
Markdown table, so the two can never silently drift. Run:

    python3 scripts/generate_registry.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "doctors.json"
OUT = ROOT / "registry" / "doctors.md"

DOCTOR_COUNT = 38
ID_RE = re.compile(r"^doct:[a-z]+(?:-[a-z]+)*$")
RP_RE = re.compile(r"^rp:[a-z]+(?:-[a-z]+)*-[ivx]+$|^rp:peter$")
MR_RE = re.compile(r"^mr:\d{4}-[a-z]+(?:-[a-z]+)*$")
TRADITIONS = {"latin", "greek", "syriac", "armenian"}

REQUIRED = (
    "number", "id", "name", "label_en", "label_la", "aliases",
    "birth_year", "death_year", "century", "birthplace", "birth_country",
    "tradition", "honorific_la", "honorific_en",
    "declared_year", "declared_by", "mr_ref", "significance", "note",
)


def load_data():
    return json.loads(DATA.read_text(encoding="utf-8"))


def validate(doc):
    entries = doc.get("entries", [])
    if doc.get("doctor_count") != DOCTOR_COUNT or len(entries) != DOCTOR_COUNT:
        raise ValueError(f"expected exactly {DOCTOR_COUNT} doctors")

    for e in entries:
        missing = [k for k in REQUIRED if k not in e]
        if missing:
            label = e.get("id", f"entry #{e.get('number', '?')}")
            raise ValueError(f"{label}: missing required key(s) {missing}")

    # number contiguity (after presence guard so a missing key is a ValueError)
    if [e["number"] for e in entries] != list(range(1, DOCTOR_COUNT + 1)):
        raise ValueError("numbers must be contiguous 1..38 in order")

    # entry order == ascending (declared_year, death_year)
    keys = [(e["declared_year"], e["death_year"]) for e in entries]
    if keys != sorted(keys):
        raise ValueError("entries must be ordered by (declared_year, death_year)")

    seen = set()
    for e in entries:
        did = e["id"]
        if not ID_RE.match(did):
            raise ValueError(f"malformed id: {did}")
        if did in seen:
            raise ValueError(f"duplicate id: {did}")
        seen.add(did)

        if e["tradition"] not in TRADITIONS:
            raise ValueError(f"{did}: tradition outside vocabulary: {e['tradition']!r}")

        if not RP_RE.match(e["declared_by"]):
            raise ValueError(f"{did}: malformed rp cross-reference: {e['declared_by']!r}")

        if e["mr_ref"] is not None and not MR_RE.match(e["mr_ref"]):
            raise ValueError(f"{did}: malformed mr_ref: {e['mr_ref']!r}")

        if (e["honorific_la"] is None) != (e["honorific_en"] is None):
            raise ValueError(f"{did}: honorific_la and honorific_en must both be set or both null")

        if e["century"] != (e["death_year"] - 1) // 100 + 1:
            raise ValueError(f"{did}: century inconsistent with death_year")

        if not isinstance(e["significance"], str) or not e["significance"].strip():
            raise ValueError(f"{did}: empty significance")


def _cell(value):
    """Escape a value for a Markdown table cell, kept to one physical line."""
    if value is None:
        return ""
    return re.sub(r"[\r\n]+", " ", str(value).replace("|", "\\|"))


def _ref(value):
    return f"`{value}`" if value else ""


def render(doc):
    entries = doc["entries"]
    lines = []
    lines.append("# Doctors of the Church")
    lines.append("")
    lines.append(
        "Canonical draft IDs for the 38 Doctors of the Church, from the four "
        "great Latin Doctors proclaimed in 1298 to St. John Henry Newman (2025), "
        "in declaration order. `#` is the declaration-sequence position; the ID is "
        "the Doctor's Latin nominative lemma (aligned with the Roman Martyrology). "
        "**Declared by** is the proclaiming pope as a [CRPDR](../../crpdr) `rp:` "
        "ID; **Eulogy** is the [CRMEDR](../../crmedr) `mr:` cross-reference to the "
        "memorial eulogy of the Roman Martyrology (empty where the saint is not in "
        "the editio typica altera 2004). All IDs are drafts pending CETF review "
        "([schema proposal](../docs/schema-proposal.md))."
    )
    lines.append("")
    header = ["#", "ID", "Doctor", "Latin", "Lived", "Tradition",
              "Honorific", "Declared", "Declared by", "Eulogy", "Significance"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for e in entries:
        lived = f"{e['birth_year']}–{e['death_year']}" if e["birth_year"] else str(e["death_year"])
        honorific = _cell(e["honorific_en"]) if e["honorific_en"] else ""
        row = [
            str(e["number"]),
            f"`{e['id']}`",
            _cell(e["name"]),
            _cell(e["label_la"]),
            _cell(lived),
            _cell(e["tradition"]),
            honorific,
            str(e["declared_year"]),
            _ref(e["declared_by"]),
            _ref(e["mr_ref"]),
            _cell(e["significance"]),
        ]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def main():
    doc = load_data()
    validate(doc)
    OUT.write_text(render(doc), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(doc['entries'])} doctors)")


if __name__ == "__main__":
    main()
