# CDOCTDR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Common DOCTors of the Church Data Repository (CDOCTDR): a hand-authored `data/doctors.json` of the 38 Doctors of the Church with canonical `doct:` Latin-lemma identifiers, a byte-deterministic generator that validates the data and renders `registry/doctors.md`, plus README, schema proposal, and tests.

**Architecture:** Mirrors the approved sibling registries CRPDR and COECDR. `data/doctors.json` is the hand-authored source of truth; `scripts/generate_registry.py` is the **sole writer** of `registry/doctors.md` and validates the data as it renders, so the table can never silently drift. Cross-references to the pope who declared each Doctor (`rp:`, CRPDR) and to the martyrology eulogy (`mr:`, CRMEDR) are validated for form always, and for existence softly (only when a sibling checkout is present).

**Tech Stack:** Python 3 standard library only (`json`, `re`, `pathlib`, `unittest`). No third-party dependencies. Byte-deterministic output.

## Global Constraints

- **Python standard library only** — no third-party imports in `scripts/`.
- **38 Doctors**, `doctor_count == 38`, `number` a contiguous `1..38`.
- **Entry order** = ascending `declared_year`, tiebroken by ascending `death_year`; `number` equals array position (1-based).
- **ID grammar:** `^doct:[a-z]+(-[a-z]+)*$` — Latin nominative lemma, ASCII-folded, lowercase, hyphenated, connectives (`de`, `a`) kept, honorific styles stripped. No bare mononyms (every Doctor carries a distinguishing epithet/cognomen).
- **`declared_by`** matches CRPDR grammar `^rp:[a-z]+(-[a-z]+)*-[ivx]+$|^rp:peter$`.
- **`mr_ref`** is `null` or matches `^mr:\d{4}-[a-z]+(-[a-z]+)*$`.
- **`tradition`** ∈ `{latin, greek, syriac, armenian}`.
- **`honorific_la` present iff `honorific_en` present** (both set, or both null).
- **`century` == `(death_year - 1) // 100 + 1`** (mechanical century-of-death).
- **License:** Apache-2.0. **Curation:** CETF of the CDCF. **All IDs are drafts pending CETF review** — every generated/authored artifact must say so.
- **Authoritative source for Latin name-forms, popes, years, honorifics:** the papal **declaration decree** of each Doctor (Task 3), not the popular English lists.
- Spec: `docs/superpowers/specs/2026-07-31-cdoctdr-design.md` (the §3.5 roster table is the working data source for Task 2).

---

### Task 1: Generator, validator, and unit tests

Build the script that validates a doctors document and renders the Markdown table, TDD'd against small synthetic fixtures (not the real 38-entry data, which arrives in Task 2). Also add the LICENSE.

**Files:**
- Create: `scripts/generate_registry.py`
- Create: `scripts/test_generate_registry.py`
- Create: `LICENSE` (Apache-2.0)

**Interfaces:**
- Consumes: nothing (first task).
- Produces:
  - `generate_registry.py` module exposing `load_data() -> dict`, `validate(doc: dict) -> None` (raises `ValueError` on any violation), `render(doc: dict) -> str`, `main() -> None`.
  - Module constants `ID_RE`, `RP_RE`, `MR_RE`, `TRADITIONS`, `DOCTOR_COUNT`.

- [ ] **Step 1: Add the Apache-2.0 LICENSE**

Copy the sibling license verbatim (identical text, Apache-2.0):

```bash
cp ../coecdr/LICENSE ./LICENSE
```

- [ ] **Step 2: Write the failing unit tests**

Create `scripts/test_generate_registry.py`. These tests build a **synthetic** minimal doc in `setUp` (two entries) so they do not depend on Task 2's data:

```python
import copy
import unittest

import generate_registry as gen


def sample_doc():
    return {
        "doctor_count": 2,
        "id_scheme": "doct:<latin-lemma>",
        "entries": [
            {
                "number": 1, "id": "doct:athanasius-alexandrinus",
                "name": "Athanasius", "label_en": "Athanasius",
                "label_la": "Athanasius Alexandrinus", "aliases": [],
                "birth_year": 298, "death_year": 373, "century": 4,
                "birthplace": "Alexandria", "birth_country": "EG",
                "tradition": "greek",
                "honorific_la": None, "honorific_en": None,
                "declared_year": 1568, "declared_by": "rp:pius-v",
                "mr_ref": "mr:0502-athanasius",
                "significance": "Champion of Nicene orthodoxy against Arianism.",
                "note": None,
            },
            {
                "number": 2, "id": "doct:thomas-de-aquino",
                "name": "Thomas Aquinas", "label_en": "Thomas Aquinas",
                "label_la": "Thomas de Aquino", "aliases": [],
                "birth_year": 1225, "death_year": 1274, "century": 13,
                "birthplace": "Roccasecca", "birth_country": "IT",
                "tradition": "latin",
                "honorific_la": "Doctor Angelicus", "honorific_en": "Angelic Doctor",
                "declared_year": 1567, "declared_by": "rp:pius-v",
                "mr_ref": "mr:0128-thomas-de-aquino",
                "significance": "Pre-eminent scholastic; author of the Summa Theologiae.",
                "note": None,
            },
        ],
    }


class TestValidate(unittest.TestCase):
    def setUp(self):
        self.doc = sample_doc()

    def test_accepts_good_doc(self):
        gen.validate(self.doc)  # must not raise

    def test_rejects_wrong_count(self):
        self.doc["doctor_count"] = 3
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_missing_required_key(self):
        del self.doc["entries"][0]["tradition"]
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_malformed_id(self):
        self.doc["entries"][0]["id"] = "doct:Athanasius"  # uppercase
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_duplicate_id(self):
        self.doc["entries"][1]["id"] = self.doc["entries"][0]["id"]
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_non_contiguous_number(self):
        self.doc["entries"][1]["number"] = 99
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_wrong_order(self):
        # swap so declared_year is descending: violates ordering rule
        self.doc["entries"].reverse()
        for i, e in enumerate(self.doc["entries"], start=1):
            e["number"] = i
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_bad_tradition(self):
        self.doc["entries"][0]["tradition"] = "coptic"
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_malformed_rp(self):
        self.doc["entries"][0]["declared_by"] = "pius-v"  # missing rp:
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_malformed_mr_ref(self):
        self.doc["entries"][0]["mr_ref"] = "mr:thomas"  # missing MMDD
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_accepts_null_mr_ref(self):
        self.doc["entries"][0]["mr_ref"] = None
        gen.validate(self.doc)  # must not raise

    def test_rejects_honorific_half_pair(self):
        self.doc["entries"][0]["honorific_la"] = "Doctor Gratiae"
        self.doc["entries"][0]["honorific_en"] = None
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_century_mismatch(self):
        self.doc["entries"][0]["century"] = 99
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_empty_significance(self):
        self.doc["entries"][0]["significance"] = "   "
        with self.assertRaises(ValueError):
            gen.validate(self.doc)


class TestRender(unittest.TestCase):
    def setUp(self):
        self.doc = sample_doc()

    def test_render_has_heading_and_all_ids(self):
        out = gen.render(self.doc)
        self.assertIn("# Doctors of the Church", out)
        for e in self.doc["entries"]:
            self.assertIn(e["id"], out)

    def test_render_escapes_pipes(self):
        self.doc["entries"][0]["significance"] = "a | b"
        out = gen.render(self.doc)
        self.assertIn("a \\| b", out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd scripts && python3 -m unittest test_generate_registry -v`
Expected: FAIL / ERROR — `ModuleNotFoundError: No module named 'generate_registry'`.

- [ ] **Step 4: Write `scripts/generate_registry.py`**

```python
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
    """Escape a value for a Markdown table cell."""
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


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
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd scripts && python3 -m unittest test_generate_registry -v`
Expected: PASS (all tests green).

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_registry.py scripts/test_generate_registry.py LICENSE
git commit -m "feat: generator, validator, and unit tests for CDOCTDR"
```

---

### Task 2: Author the seed data and generate the registry table

Hand-author all 38 Doctor records into `data/doctors.json` from the spec's §3.5 roster, add a data-invariant test file (including soft cross-registry existence checks), and generate `registry/doctors.md`.

**Files:**
- Create: `data/doctors.json`
- Create: `scripts/test_doctors_data.py`
- Create: `registry/doctors.md` (generated — do not hand-edit)

**Interfaces:**
- Consumes: `generate_registry.validate/render` and its constants from Task 1.
- Produces: `data/doctors.json` conforming to the Global Constraints; `registry/doctors.md`.

- [ ] **Step 1: Author `data/doctors.json`**

Top-level shape (fill `entries` with all 38, in the order and with the ids/popes/years/mr_refs/traditions from spec §3.5):

```json
{
  "$comment": "CDOCTDR seed registry: draft canonical IDs for the 38 Doctors of the Church. Original compilation in the registry's own words; Latin name-forms follow the Roman Martyrology (CRMEDR) and the papal declaration decrees. All IDs and fields are drafts pending CETF review (docs/schema-proposal.md).",
  "id_scheme": "doct:<latin-lemma> (Latin nominative lemma, aligned with CRMEDR)",
  "sources": {
    "note": "Background reading only; no third-party table is captured. The declaration decrees are the authority for Latin name-forms, popes, years, and honorifics.",
    "references": [
      "https://uscatholic.org/articles/200807/chronological-list-of-the-doctors-of-the-church/",
      "https://aleteia.org/2026/07/19/heres-a-full-list-of-all-the-doctors-of-the-church/",
      "https://www.britannica.com/topic/list-of-doctors-of-the-church-2068542",
      "https://www.nashvillecatholic.org/news/posts/who-are-the-doctors-of-the-catholic-church"
    ]
  },
  "doctor_count": 38,
  "entries": [ ... 38 records ... ]
}
```

Author each record with **all 19 required keys** (Task 1 `REQUIRED`). Use spec §3.5 for `id`, `name`, life-dates, `declared_year`, `declared_by`, `mr_ref`, and `tradition`; write an **original** 1–2 sentence `significance`; supply `label_la` (the Latin nominative form the slug derives from), `label_en` (= `name` unless a shorter display form is wanted), `aliases`, `birthplace`, `birth_country` (ISO 3166-1 alpha-2), and `honorific_la`/`honorific_en` (both null where no traditional epithet). Set `century = (death_year - 1)//100 + 1`. Put approximate-date and East–West notes in `note`. Two fully-worked records to follow (from spec §3.4):

```json
{
  "number": 5,
  "id": "doct:thomas-de-aquino",
  "name": "Thomas Aquinas",
  "label_en": "Thomas Aquinas",
  "label_la": "Thomas de Aquino",
  "aliases": ["Thomas of Aquino"],
  "birth_year": 1225, "death_year": 1274, "century": 13,
  "birthplace": "Roccasecca", "birth_country": "IT",
  "tradition": "latin",
  "honorific_la": "Doctor Angelicus", "honorific_en": "Angelic Doctor",
  "declared_year": 1567, "declared_by": "rp:pius-v",
  "mr_ref": "mr:0128-thomas-de-aquino",
  "significance": "The pre-eminent scholastic theologian; his synthesis of faith and reason in the Summa Theologiae shaped Catholic theology and was commended by Leo XIII as a model for study.",
  "note": null
},
{
  "number": 38,
  "id": "doct:ioannes-henricus-newman",
  "name": "John Henry Newman",
  "label_en": "John Henry Newman",
  "label_la": "Ioannes Henricus Newman",
  "aliases": ["John Henry Cardinal Newman"],
  "birth_year": 1801, "death_year": 1890, "century": 19,
  "birthplace": "London", "birth_country": "GB",
  "tradition": "latin",
  "honorific_la": null, "honorific_en": null,
  "declared_year": 2025, "declared_by": "rp:leo-xiv",
  "mr_ref": null,
  "significance": "Convert from Anglicanism, cardinal, and theologian of conscience, doctrinal development, and the harmony of faith and reason; proclaimed a Doctor of the Church on All Saints' Day 2025.",
  "note": "Canonized 2019, after the editio typica altera (2004); absent from CRMEDR, so mr_ref is null pending a future edition."
}
```

The complete id / pope / year / mr_ref / tradition values for all 38 rows are the spec's §3.5 table — transcribe them exactly, prefixing each `declared_by` with `rp:` (e.g. `rp:boniface-viii`, `rp:pius-v`, `rp:leo-xiii`, `rp:francis-i`, `rp:leo-xiv`).

- [ ] **Step 2: Write the data-invariant tests**

Create `scripts/test_doctors_data.py`:

```python
import json
import re
import unittest
from collections import Counter
from pathlib import Path

import generate_registry as gen

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "doctors.json"


class TestDoctorsData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(DATA.read_text(encoding="utf-8"))
        cls.entries = cls.doc["entries"]

    def test_validates_against_generator(self):
        gen.validate(self.doc)  # the real data must satisfy every rule

    def test_count_is_38(self):
        self.assertEqual(self.doc["doctor_count"], 38)
        self.assertEqual(len(self.entries), 38)

    def test_ids_unique_and_well_formed(self):
        ids = [e["id"] for e in self.entries]
        self.assertEqual(len(ids), len(set(ids)), "duplicate ids")
        for i in ids:
            self.assertRegex(i, gen.ID_RE, f"malformed id: {i}")

    def test_no_bare_mononyms(self):
        # rule 1: every slug carries a distinguishing epithet (a hyphen)
        for e in self.entries:
            self.assertIn("-", e["id"].split(":", 1)[1], f"{e['id']}: bare mononym")

    def test_order_by_declared_then_death(self):
        keys = [(e["declared_year"], e["death_year"]) for e in self.entries]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual([e["number"] for e in self.entries], list(range(1, 39)))

    def test_tradition_vocabulary(self):
        for e in self.entries:
            self.assertIn(e["tradition"], gen.TRADITIONS, f"{e['id']}: {e['tradition']}")

    def test_tradition_distribution(self):
        # sanity floor: the non-Latin Doctors are present and singular where expected
        counts = Counter(e["tradition"] for e in self.entries)
        self.assertEqual(counts["syriac"], 1)    # Ephrem
        self.assertEqual(counts["armenian"], 1)  # Gregory of Narek
        self.assertGreaterEqual(counts["greek"], 7)
        self.assertEqual(sum(counts.values()), 38)

    def test_rp_crossrefs_well_formed(self):
        for e in self.entries:
            self.assertRegex(e["declared_by"], gen.RP_RE, f"{e['id']}: {e['declared_by']}")

    def test_mr_refs_well_formed_or_null(self):
        for e in self.entries:
            if e["mr_ref"] is not None:
                self.assertRegex(e["mr_ref"], gen.MR_RE, f"{e['id']}: {e['mr_ref']}")

    def test_honorific_pairing(self):
        for e in self.entries:
            self.assertEqual(e["honorific_la"] is None, e["honorific_en"] is None,
                             f"{e['id']}: honorific pair mismatch")

    def test_significance_present(self):
        for e in self.entries:
            self.assertTrue(e["significance"].strip(), f"{e['id']}: empty significance")

    def test_declared_by_exists_in_crpdr(self):
        crpdr = ROOT.parent / "crpdr" / "data" / "pontiffs.json"
        if not crpdr.exists():
            self.skipTest("crpdr checkout not present")
        pope_ids = {p["id"] for p in json.loads(crpdr.read_text(encoding="utf-8"))["entries"]}
        for e in self.entries:
            self.assertIn(e["declared_by"], pope_ids, f"{e['id']}: {e['declared_by']} not in CRPDR")

    def test_mr_ref_exists_in_crmedr(self):
        crmedr = ROOT.parent / "crmedr" / "data" / "martyrology_ids.json"
        if not crmedr.exists():
            self.skipTest("crmedr checkout not present")
        mr_ids = {x["id"] for x in json.loads(crmedr.read_text(encoding="utf-8"))["entries"]}
        for e in self.entries:
            if e["mr_ref"] is not None:
                self.assertIn(e["mr_ref"], mr_ids, f"{e['id']}: {e['mr_ref']} not in CRMEDR")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the data tests**

Run: `cd scripts && python3 -m unittest test_doctors_data -v`
Expected: PASS. The two cross-registry tests will either pass (siblings present) or `skip` — both acceptable. If `test_mr_ref_exists_in_crmedr` **fails**, a `mr_ref` value is wrong; fix it in `data/doctors.json` against CRMEDR (Task 3 verifies these systematically).

- [ ] **Step 4: Generate the registry table**

Run: `python3 scripts/generate_registry.py`
Expected: prints `wrote registry/doctors.md (38 doctors)` and no exception.

- [ ] **Step 5: Run the full suite**

Run: `python3 -m unittest discover -s scripts -v`
Expected: PASS (unit + data tests).

- [ ] **Step 6: Commit**

```bash
git add data/doctors.json scripts/test_doctors_data.py registry/doctors.md
git commit -m "feat: seed 38 Doctor records and generate registry table"
```

---

### Task 3: Decree & CRMEDR verification pass

Reconcile the working data against authoritative primary sources: each Doctor's **declaration decree** (for Latin name-form, pope, year, honorific) and CRMEDR (for the exact `mr_ref`). This resolves spec open questions #1, #2, #5.

**Files:**
- Modify: `data/doctors.json`
- Modify: `registry/doctors.md` (regenerated)

**Interfaces:**
- Consumes: the data from Task 2.
- Produces: verified `data/doctors.json` (unchanged shape).

- [ ] **Step 1: Verify every `mr_ref` against CRMEDR**

For each non-null `mr_ref`, confirm the exact id exists in `../crmedr/data/martyrology_ids.json` (the memorial-day entry). Use:

```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path("../crmedr/data/martyrology_ids.json")
mr = {x["id"] for x in json.loads(root.read_text())["entries"]}
doc = json.loads(Path("data/doctors.json").read_text())
for e in doc["entries"]:
    ref = e["mr_ref"]
    flag = "OK " if ref is None or ref in mr else "MISS"
    print(flag, e["id"], "->", ref)
PY
```

Fix any `MISS` by locating the saint's memorial-day entry in CRMEDR (grep `i18n/la.json` for the Latin name) and setting `mr_ref` to that exact id. Confirm the known `*`-marked rows from spec §3.5: `mr:0913-ioannes-chrysostomus` (or CRMEDR's actual John Chrysostom memorial id), `mr:1110-leo-i`, `mr:0801-alfonsus-maria-de-ligorio`, `mr:1204-ioannes-damasceni`, `mr:0917-robertus-bellarmino`, `mr:0510-ioannes-de-abula`, and `mr:1207-ambrosius`.

- [ ] **Step 2: Verify Latin name-forms, popes, years, and honorifics against the declaration decrees**

For each Doctor, confirm against the proclamation decree (papal bull / apostolic letter). Priorities flagged in the spec:
- **Robert Bellarmine** — confirm `doct:robertus-bellarminus` (classical `-us`) is the decree's form; keep `mr_ref` at CRMEDR's `robertus-bellarmino`.
- **Alphonsus Liguori** — confirm the decree spelling of `alphonsus-maria-de-ligorio` (vs CRMEDR's `alfonsus-...`).
- **Hilary of Poitiers** — confirm `declared_year` (1851, Pius IX; the popular list's "1831" is a likely typo).
- **Honorifics** — fill `honorific_la`/`honorific_en` where a traditional title exists (e.g. Aquinas *Doctor Angelicus*, Augustine *Doctor Gratiae*, Bernard *Doctor Mellifluus*, Bonaventure *Doctor Seraphicus*, John of the Cross *Doctor Mysticus*, Irenaeus *Doctor unitatis*), leaving both null otherwise.

Record any decision that departs from CRMEDR's form (and any CRMEDR normalization to propose) in `docs/schema-proposal.md` open questions during Task 4.

- [ ] **Step 3: Regenerate and re-test**

Run: `python3 scripts/generate_registry.py && python3 -m unittest discover -s scripts -v`
Expected: `wrote registry/doctors.md (38 doctors)` then PASS.

- [ ] **Step 4: Commit**

```bash
git add data/doctors.json registry/doctors.md
git commit -m "fix: verify Latin forms, popes, years, honorifics, and mr_refs against decrees and CRMEDR"
```

---

### Task 4: README and schema proposal

Author the two prose documents, following the COECDR pattern (`../coecdr/README.md`, `../coecdr/docs/schema-proposal.md`) in structure and tone.

**Files:**
- Create: `README.md`
- Create: `docs/schema-proposal.md`

**Interfaces:**
- Consumes: the finished data and the design spec.
- Produces: repository-root docs (no code contract).

- [ ] **Step 1: Write `README.md`**

Sections (mirror COECDR): title + one-line CETF/CDCF attribution; **What is CDOCTDR?** (38 Doctors, 1298→Newman 2025, restrictive title); **Why?** (unambiguous doctrinal/catechetical reference; cross-refs to declaring pope and martyrology eulogy); **The identifier scheme (draft)** (the `doct:<latin-lemma>` grammar, Latin-lemma rationale, CRMEDR alignment, "All IDs are drafts pending committee review"); **Relationship to sibling registries** (CRMEDR `mr_ref`, CRPDR `declared_by`, the Latin-vs-English source principle); **Repository contents** (bullet list of `data/doctors.json`, `registry/doctors.md`, `docs/schema-proposal.md`, `scripts/`); **Sources** (original compilation; the four links are background; the decrees are authoritative for Latin forms). Draw prose from the spec §1.

- [ ] **Step 2: Write `docs/schema-proposal.md`**

Sections (mirror COECDR): **Status** (Draft, pending CETF review); **1. Identifier grammar** (ABNF from spec §2.2 + the derivation rules §2.1: full appellation, decree form, CRMEDR alignment with uniqueness promotion, nominative normalization, Doctor-vs-pope frame); **2. Data fields** (the field table from spec §3, including `label_la`, `honorific_la/en`, `tradition`, `declared_by`, `mr_ref`); **3. Ordering** (declared_year, death-year tiebreak; `number` is presentation order, not a magisterial rank); **4. Open questions** (spec §5: CRMEDR normalizations, decree verification, Irenaeus `tradition`, `cdcf_person`, honorific sourcing). End with "All IDs and fields are drafts pending CETF review."

- [ ] **Step 3: Sanity-check internal links**

Run: `grep -o '](\.\.\?/[^)]*)' README.md docs/schema-proposal.md`
Expected: relative links resolve (`docs/schema-proposal.md`, `data/doctors.json`, `registry/doctors.md`, `../crmedr`, `../crpdr`). Fix any that don't.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/schema-proposal.md
git commit -m "docs: README and schema proposal"
```

---

### Task 5: Final verification and handoff

**Files:** none created; verification and optional remote setup.

**Interfaces:**
- Consumes: the whole repository.
- Produces: a green build and a push-ready repository.

- [ ] **Step 1: Confirm the generator output is committed and in sync**

Run: `python3 scripts/generate_registry.py && git status --porcelain`
Expected: `wrote registry/doctors.md (38 doctors)` and **empty** git status (regeneration produced no diff — the committed table matches the data).

- [ ] **Step 2: Run the full test suite**

Run: `python3 -m unittest discover -s scripts -v`
Expected: all tests PASS (cross-registry tests pass if `../crpdr` and `../crmedr` are present, else skip).

- [ ] **Step 3: Verify the deliverables exist**

Run: `ls README.md LICENSE data/doctors.json registry/doctors.md docs/schema-proposal.md scripts/generate_registry.py scripts/test_generate_registry.py scripts/test_doctors_data.py`
Expected: all listed, no "No such file".

- [ ] **Step 4: Hand off remote creation to the user**

Do **not** create the GitHub repository autonomously. Report readiness and propose the command for the user to run (e.g. `gh repo create CatholicOS/cdoctdr --public --source=. --remote=origin --push`), matching how the sibling registries were published under the CatholicOS org.

---

## Self-Review

**Spec coverage:**
- §1 purpose / originality / decrees-authoritative → Task 2 (sources block), Task 3 (decree pass), Task 4 (README/schema prose). ✓
- §1.2 sibling relationships (`mr_ref`, `declared_by`, language principle) → data fields (Task 2), soft cross-checks (Task 2 tests), prose (Task 4). ✓
- §2 identifier scheme + grammar + rules 1–5 → `ID_RE` + `test_no_bare_mononyms` (Tasks 1–2), decree/normalization handling (Task 3), schema prose (Task 4). ✓
- §3 data model (all 19 fields, `label_la`, honorific pairing, tradition vocab, ordering, century rule) → `REQUIRED` + `validate` (Task 1), data + data-tests (Task 2). ✓
- §3.2 `mr_ref` nulls (Narek, Newman) + joint eulogy (Basil/Greg Naz) → `test_accepts_null_mr_ref` (Task 1), authored data + CRMEDR check (Tasks 2–3). ✓
- §3.3 ordering & `number` → `test_order_by_declared_then_death`, `validate` order check. ✓
- §3.5 roster (38 ids/popes/years/mr_refs/traditions) → Task 2 Step 1 transcription. ✓
- §4 repo layout + sole-writer generator + soft cross-checks + tests → Tasks 1, 2, 5. ✓
- §5 open questions → Task 3 (decrees, CRMEDR normalizations, Irenaeus, honorifics), Task 4 (schema-proposal open-questions section). ✓

**Placeholder scan:** No TBD/TODO. The one inherently-authored artifact — the 38 `significance` prose strings — has an explicit pattern, two fully-worked examples, and the exact factual source (spec §3.5); this is authoring, not a placeholder. ✓

**Type consistency:** `validate`/`render`/`load_data`/`main` and constants `ID_RE`/`RP_RE`/`MR_RE`/`TRADITIONS`/`DOCTOR_COUNT` are defined in Task 1 and referenced by identical names in Task 2's tests. The 19 `REQUIRED` keys match the authored record shape and the two worked examples. `mr_ref`/`declared_by` regexes are consistent across generator and data tests. ✓
