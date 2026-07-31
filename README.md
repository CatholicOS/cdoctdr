# CDOCTDR

The home of the **Common DOCTors of the Church Data Repository**, curated by the
**Catholic Engineering Task Force** of the
[Catholic Digital Commons Foundation](https://github.com/CatholicOS).

## What is CDOCTDR?

The Common DOCTors of the Church Data Repository (CDOCTDR) provides canonical,
stable identifiers for the **thirty-eight Doctors of the Church**, from the four
great Latin Doctors proclaimed by Boniface VIII in 1298 to **St. John Henry
Newman**, proclaimed in 2025.

The title *Doctor of the Church* (*Doctor Ecclesiae*) is a formal, restrictive
distinction conferred by the Roman Pontiff (or an ecumenical council) on a saint
whose writings are of eminent doctrinal value for the whole Church. This registry
catalogues those saints so distinguished, and no others; it is not a general
registry of theologians, Fathers, or saints.

## Why?

Canonical Doctor identifiers are needed wherever Catholic data must reference a
Doctor of the Church unambiguously: magisterial and catechetical attribution,
patristic and theological datasets, reference works, and cross-references from
sibling registries — the pope who declared a Doctor
([CRPDR](https://github.com/CatholicOS/crpdr)) and the saint's own martyrology
eulogy ([CRMEDR](https://github.com/CatholicOS/crmedr)).

## The identifier scheme (draft)

```text
doct:<latin-lemma>     e.g. doct:thomas-de-aquino, doct:ioannes-a-cruce
```

The slug is the Doctor's **Latin nominative lemma**: ASCII-folded, lowercased,
spaces hyphenated, honorific styles (*sanctus* / *beatus*) removed, and Latin
connective particles (`de`, `a`) retained. Every slug carries the Doctor's full
conventional appellation — a toponym, cognomen, or religious name — so there are
no bare mononyms: Augustine of Hippo is `doct:augustinus-hipponensis`, never
`doct:augustinus`. This maximises resolution and future-proofs the namespace
against a later Doctor of the same base name.

Where CRMEDR already carries the same saint, CDOCTDR reuses its Latin lemma, with
two adjustments: a lemma not globally unique among the 38 Doctors is promoted
with its epithet (the two Cyrils), and an inflected eulogy form is normalized to
the clean nominative (`doct:ioannes-chrysostomus`, not the eulogy's genitive
*chrysostomi*). The full grammar and derivation rules are in
[docs/schema-proposal.md](docs/schema-proposal.md). **All IDs are drafts pending
committee review.**

## Relationship to sibling registries

CDOCTDR sits deliberately between two siblings and links to both. Each per-record
`mr_ref` cross-references [CRMEDR](https://github.com/CatholicOS/crmedr)'s `mr:`
identifier for the Doctor's memorial eulogy in the Roman Martyrology; each
`declared_by` cross-references [CRPDR](https://github.com/CatholicOS/crpdr)'s
`rp:` identifier for the proclaiming pope.

**Why `doct:` slugs are Latin while sibling `rp:` slugs are English.** Each
registry's slug language follows *its own authoritative source*: the Vatican's
English regnal table for CRPDR, and the Latin *Martyrologium* / Latin declaration
decrees for CRMEDR and CDOCTDR. A saint who is also a pope thus appears under
both conventions, bridged by cross-references — e.g. Gregory the Great is
`rp:gregory-i` (CRPDR), `doct:gregorius-magnus` (CDOCTDR), and
`mr:0903-gregorius-magnus` (CRMEDR). This is a feature, not an inconsistency: the
identifier honours the source that defines the entity in each context.

## Repository contents

- [`data/doctors.json`](data/doctors.json) — the hand-authored source of truth:
  38 Doctor records, each with its draft canonical ID, English and Latin names,
  life-dates, tradition, honorific title, declaration year and proclaiming pope
  (`declared_by`), a martyrology cross-reference (`mr_ref`), and an original
  significance summary.
- [`registry/doctors.md`](registry/doctors.md) — the same registry as a
  human-readable table, one row per Doctor in declaration order.
- [`docs/schema-proposal.md`](docs/schema-proposal.md) — the proposed schema, the
  identifier grammar, and the open questions for the committee.
- [`scripts/`](scripts/) — `generate_registry.py` regenerates the table
  (`python3 scripts/generate_registry.py`) and validates the data as it renders;
  tests: `python3 -m unittest discover -s scripts`.

## Sources

CDOCTDR is an original compilation: the list, dates, and prose significance
summaries are authored by the registry in its own words. Convenient online lists
(US Catholic, Aleteia, Britannica, Nashville Catholic) are used only as
**background reading**; no third-party table is captured or quoted verbatim.

The one genuinely authoritative primary source is each Doctor's **declaration
decree** (papal bull or apostolic letter), which fixes the Latin name-form, the
year and proclaiming pope, and often the traditional Latin honorific. These
decrees, not the popular lists, are the reference for the Latin name-forms and
the `declared_by` / `declared_year` / `honorific_la` values in this registry.
