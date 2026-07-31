# CDOCTDR — Common DOCTors of the Church Data Repository: Design

**Date:** 2026-07-31
**Status:** Approved design, pending implementation
**Repository:** `CatholicOS/cdoctdr`
**Curation:** Catholic Engineering Task Force (CETF) of the Catholic Digital Commons Foundation (CDCF)
**License:** Apache-2.0

## 1. Purpose

CDOCTDR provides canonical, stable identifiers for the **thirty-eight Doctors of
the Church**, from the four great Latin Doctors proclaimed by Boniface VIII in
1298 to **St. John Henry Newman** (2025), for use wherever Catholic data must
reference a Doctor of the Church unambiguously: magisterial and catechetical
attribution, patristic and theological datasets, reference works, and
cross-references from sibling registries (the declaring pope, the saint's
martyrology eulogy).

The title *Doctor of the Church* (*Doctor Ecclesiae*) is a formal, restrictive
distinction conferred by the Roman Pontiff (or an ecumenical council) on a saint
whose writings are of eminent doctrinal value for the whole Church. The registry
catalogues those saints so distinguished and no others; it is not a general
registry of theologians, Fathers, or saints.

### 1.1 Sourcing and originality

Like [COECDR](https://github.com/CatholicOS/coecdr) — and unlike
[CRPDR](https://github.com/CatholicOS/crpdr), which snapshots the Holy See's own
reference table — CDOCTDR has **no single authoritative tabulation** to capture.
The roster, life-dates, and doctrinal summaries are matters of public record; the
convenient online lists (US Catholic, Aleteia, Britannica, Nashville Catholic)
are used only as **background reading**. CDOCTDR is therefore an **original
compilation**: the list, dates, prose `significance` summaries, and metadata are
authored by the registry in its own words. No third-party table is captured or
quoted verbatim; there is no `data/source/` snapshot and no copyright constraint
of the kind that governs the martyrology texts.

There is, however, one class of genuinely **authoritative** primary source: the
**declaration decree** (papal bull or apostolic letter) that proclaims each
Doctor. Being an act of the Magisterium, each such decree exists in an official
**Latin** form that fixes (a) the Doctor's Latin name, (b) the year and the
proclaiming pope, and frequently (c) the traditional Latin honorific title. These
decrees — not the popular English lists — are the reference for the Latin
name-forms, the `declared_by`/`declared_year` values, and the `honorific_la`
field. Verifying each Doctor's data against its decree is an explicit task of the
implementation plan (§4, open question 2).

### 1.2 Relationship to the sibling registries

CDOCTDR sits deliberately between two siblings and links to both:

- **CRMEDR** ([martyrology](https://github.com/CatholicOS/crmedr)) — the Doctors
  are the very saints CRMEDR already catalogues. CDOCTDR therefore **borrows
  CRMEDR's identifier convention** (the Latin nominative lemma, §2) and carries a
  per-record `mr_ref` cross-reference to the Doctor's memorial eulogy. The two
  registries speak the same onomastic language on purpose.
- **CRPDR** ([Roman Pontiffs](https://github.com/CatholicOS/crpdr)) — every Doctor
  was proclaimed by a pope, recorded as a `declared_by` `rp:` cross-reference,
  exactly as COECDR records the pope who convened or confirmed a council.

**Why `doct:` slugs are Latin while sibling `rp:` slugs are English.** Each
registry's slug language follows *its own authoritative source*: the Vatican's
English regnal table for CRPDR, and the Latin *Martyrologium* / Latin declaration
decrees for CRMEDR and CDOCTDR. A saint who is also a pope thus appears under both
conventions, bridged by cross-references — e.g. Gregory the Great is
`rp:gregory-i` (CRPDR), `doct:gregorius-magnus` (CDOCTDR), and
`mr:0903-gregorius-magnus` (CRMEDR). This is a feature, not an inconsistency: the
identifier honours the source that defines the entity in each context.

## 2. Identifier scheme

```
doct:<latin-lemma>        e.g. doct:thomas-de-aquino, doct:ioannes-a-cruce
```

The slug is the **Latin nominative lemma** of the Doctor, following CRMEDR's
derivation rule: ASCII-folded (diacritics stripped), lowercased, spaces
hyphenated, honorific styles (*sanctus* / *beatus*) removed, Latin connective
particles (`de`, `a`) **retained**. Examples: `doct:thomas-de-aquino`,
`doct:ioannes-a-cruce`, `doct:catharina-senensis`, `doct:beda-venerabilis`.

### 2.1 Rules

1. **Full conventional appellation.** Every Doctor's slug carries the Doctor's
   conventional distinguishing epithet — a toponym (`hipponensis`, `senensis`,
   `bingensis`, `pictaviensis`, `lugdunensis`), a cognomen (`magnus`,
   `chrysologus`, `chrysostomus`, `venerabilis`), or a religious name
   (`a-iesu`, `a-cruce`). There are **no bare mononyms**: Augustine of Hippo is
   `doct:augustinus-hipponensis`, not `doct:augustinus`; Ambrose is
   `doct:ambrosius-mediolanensis`. This maximises resolution and future-proofs
   the namespace against a later Doctor of the same base name.
2. **Latin form from the declaration decree.** Where the Latin proclamation decree
   fixes a name-form, that form governs. The registry therefore uses the classical
   `doct:robertus-bellarminus` and `doct:leo-magnus`, verified against the decrees
   during implementation.
3. **CRMEDR alignment, with promotion for global uniqueness.** Where CRMEDR
   already carries the same saint, reuse its lemma. But CRMEDR IDs are
   **date-scoped** (`mr:MMDD-slug`), so CRMEDR can keep two homonyms apart by
   their calendar day; `doct:` IDs are **not** date-scoped, so any lemma that is
   not globally unique among the 38 Doctors must be **promoted** with its epithet.
   Forced case: the two Cyrils — `doct:cyrillus-hierosolymitanus` and
   `doct:cyrillus-alexandrinus` (CRMEDR: bare `cyrillus` on 03-18 and 06-27).
4. **Nominative normalization.** Where a CRMEDR eulogy text carries a per-entry
   grammatical inflection, the `doct:` slug is the clean nominative:
   `doct:ioannes-chrysostomus` (CRMEDR text *…chrysostomi*),
   `doct:ioannes-damascenus` (CRMEDR text *…damasceni*). The `mr_ref` field still
   points at CRMEDR's actual id, so the hard link is preserved.
5. **Identifying-as-a-Doctor, not-as-a-pope.** Where CRMEDR identifies a
   saint-pope by regnal ordinal (`mr:1110-leo-i`), CDOCTDR identifies the same
   person *in his capacity as a Doctor* by his doctoral cognomen:
   `doct:leo-magnus`. The `mr_ref` bridges the two frames.

### 2.2 Grammar (ABNF, per RFC 5234)

```abnf
doctor-id    = "doct:" lemma
lemma        = lowercase *( lowercase / "-" ) lowercase
lowercase    = %x61-7A                        ; a-z
```

`^doct:[a-z]+(-[a-z]+)*$`

## 3. Data model

`data/doctors.json` is the **hand-authored source of truth**: a JSON object with
registry metadata and an `entries` array of thirty-eight Doctor records, in
declaration order (§3.3). Each record:

| field | type | meaning |
| --- | --- | --- |
| `number` | integer 1–38 | position in the declaration sequence (§3.3) |
| `id` | string | the `doct:` canonical identifier |
| `name` | string | the Doctor's common English name ("Augustine of Hippo") |
| `label_en` | string | English display label (may equal `name`) |
| `label_la` | string | Latin nominative display form ("Augustinus Hipponensis") — the provenance of the slug |
| `aliases` | array of string | alternative names ("Albertus Magnus", "Doctor Angelicus" is *not* an alias — see `honorific_*`) |
| `birth_year` | integer \| null | year of birth (approximate for antiquity → `note`) |
| `death_year` | integer \| null | year of death |
| `century` | integer | century of death (the era to which the Doctor belongs) |
| `birthplace` | string \| null | place of birth |
| `birth_country` | string \| null | ISO 3166-1 alpha-2 of the modern country of that place |
| `tradition` | string | ecclesial/cultural tradition, controlled vocabulary `latin` / `greek` / `syriac` / `armenian` (§3.1) |
| `honorific_la` | string \| null | traditional Latin honorific ("Doctor Angelicus", "Doctor Gratiae", "Doctor unitatis") — null where none is traditional |
| `honorific_en` | string \| null | English form of the honorific ("Angelic Doctor", "Doctor of Grace", "Doctor of Unity") |
| `declared_year` | integer | year proclaimed a Doctor of the Church |
| `declared_by` | string | CRPDR `rp:` cross-reference to the proclaiming pope |
| `mr_ref` | string \| null | CRMEDR `mr:` cross-reference to the Doctor's memorial eulogy; null if the saint is absent from the *editio typica altera 2004* (§3.2) |
| `significance` | string | brief, original-wording summary of the Doctor's doctrinal contribution |
| `note` | string \| null | disambiguation or context (approximate dates, East–West position, decree particulars) |

Top-level metadata mirrors the siblings: a `$comment` (draft-status notice),
`id_scheme`, a `sources` array (background references, explicitly marked
non-authoritative), and `doctor_count` (38).

### 3.1 The `tradition` vocabulary

A single controlled value per Doctor, supporting Britannica's grouping by
cultural origin and surfacing the non-Latin Doctors:

| value | Doctors | count |
| --- | --- | --- |
| `latin` | the Western Doctors (Ambrose … Newman) | 28 |
| `greek` | Athanasius, Basil, Gregory of Nazianzus, John Chrysostom, the two Cyrils, John Damascene (and, provisionally, Irenaeus) | 7–8 |
| `syriac` | Ephrem | 1 |
| `armenian` | Gregory of Narek | 1 |

Finer nuance (Antiochene vs Alexandrine formation, Newman's convert path, a
Doctor who wrote in Greek but served a Western see) is carried in prose
(`note` / `significance`), never multiplied into the enum. **Irenaeus of Lyon**
is the one open assignment: `greek` by language and patristic lineage, `latin` by
his see of Lyon; the design defaults to `greek` and records the East–West bridge
(the ground of his honorific *Doctor unitatis*) in `note` — see §5.

### 3.2 `mr_ref` and the living Martyrology

`mr_ref` links each Doctor to the memorial eulogy of the *Martyrologium Romanum*
(CRMEDR). It is `null` for Doctors whose saints are **not in the editio typica
altera (2004)** that anchors CRMEDR — presently **Gregory of Narek** (an Armenian
saint outside the Roman Martyrology) and **John Henry Newman** (canonized 2019,
after the 2004 edition). Two Doctors — **Basil the Great** and **Gregory of
Nazianzus** — share a single **joint** memorial eulogy (2 January); both records'
`mr_ref` point to it (a many-to-one reference is expected). Because the
Martyrology is a living source and CDOCTDR's own Latin forms are sometimes finer
or more classical than CRMEDR's per-eulogy text, `mr_ref` is understood to
**track CRMEDR** and may be re-aligned when either registry is revised (§5,
open question 1).

### 3.3 Ordering and the `number` field

Entries are ordered by **`declared_year`**, with a deterministic within-year
tiebreak by **`death_year`** (earliest first). This resolves the six years in
which more than one Doctor was proclaimed (1298 ×4, 1568 ×4, 1883 ×2, 1931 ×2,
1970 ×2, 2012 ×2) and happens to reproduce the conventional listings. `number` is
the declaration-sequence position 1–38; there is no official Holy See ordinal, so
`number` is the registry's own presentation order, not a magisterial rank.

### 3.4 Worked examples

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
  "note": "Canonized 2019, after the editio typica altera (2004); absent from CRMEDR, so mr_ref is null pending a future edition. honorific_* null pending any title fixed by the declaration decree."
}
```

### 3.5 The thirty-eight Doctors and their identifiers

| # | `doct:` id | Doctor | lived | decl. | pope (`rp:`) | `mr_ref` | trad. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `ambrosius-mediolanensis` | Ambrose | 340–397 | 1298 | boniface-viii | `mr:1207-ambrosius` | latin |
| 2 | `hieronymus-stridonensis` | Jerome | 347–420 | 1298 | boniface-viii | `mr:0930-hieronymus` | latin |
| 3 | `augustinus-hipponensis` | Augustine of Hippo | 354–430 | 1298 | boniface-viii | `mr:0828-augustinus` | latin |
| 4 | `gregorius-magnus` | Gregory the Great | 540–604 | 1298 | boniface-viii | `mr:0903-gregorius-magnus` | latin |
| 5 | `thomas-de-aquino` | Thomas Aquinas | 1225–1274 | 1567 | pius-v | `mr:0128-thomas-de-aquino` | latin |
| 6 | `athanasius-alexandrinus` | Athanasius | 298–373 | 1568 | pius-v | `mr:0502-athanasius` | greek |
| 7 | `basilius-magnus` | Basil the Great | 330–379 | 1568 | pius-v | `mr:0102-basilius-magnus-et-gregorius-nazianzenus` ‡ | greek |
| 8 | `gregorius-nazianzenus` | Gregory of Nazianzus | 329–390 | 1568 | pius-v | `mr:0102-basilius-magnus-et-gregorius-nazianzenus` ‡ | greek |
| 9 | `ioannes-chrysostomus` | John Chrysostom | 347–407 | 1568 | pius-v | `mr:0913-ioannes-chrysostomus` * | greek |
| 10 | `bonaventura-de-balneoregio` | Bonaventure | 1221–1274 | 1588 | sixtus-v | `mr:0715-bonaventura` | latin |
| 11 | `anselmus-cantuariensis` | Anselm of Canterbury | 1033–1109 | 1720 | clement-xi | `mr:0421-anselmus` | latin |
| 12 | `isidorus-hispalensis` | Isidore of Seville | 560–636 | 1722 | innocent-xiii | `mr:0404-isidorus` | latin |
| 13 | `petrus-chrysologus` | Peter Chrysologus | 406–450 | 1729 | benedict-xiii | `mr:0730-petrus-chrysologus` | latin |
| 14 | `leo-magnus` | Leo the Great | 400–461 | 1754 | benedict-xiv | `mr:1110-leo-i` * | latin |
| 15 | `petrus-damianus` | Peter Damian | 1007–1072 | 1828 | leo-xii | `mr:0221-petrus-damianus` | latin |
| 16 | `bernardus-claraevallensis` | Bernard of Clairvaux | 1090–1153 | 1830 | pius-viii | `mr:0820-bernardus` | latin |
| 17 | `hilarius-pictaviensis` | Hilary of Poitiers | 300–367 | 1851 | pius-ix | `mr:0113-hilarius` | latin |
| 18 | `alphonsus-maria-de-ligorio` | Alphonsus Liguori | 1696–1787 | 1871 | pius-ix | `mr:0801-alfonsus-maria-de-ligorio` * | latin |
| 19 | `franciscus-de-sales` | Francis de Sales | 1567–1622 | 1877 | pius-ix | `mr:0124-franciscus-de-sales` | latin |
| 20 | `cyrillus-hierosolymitanus` | Cyril of Jerusalem | 315–386 | 1883 | leo-xiii | `mr:0318-cyrillus` | greek |
| 21 | `cyrillus-alexandrinus` | Cyril of Alexandria | 376–444 | 1883 | leo-xiii | `mr:0627-cyrillus` | greek |
| 22 | `ioannes-damascenus` | John Damascene | 676–749 | 1890 | leo-xiii | `mr:1204-ioannes-damasceni` * | greek |
| 23 | `beda-venerabilis` | Bede the Venerable | 672–735 | 1899 | leo-xiii | `mr:0525-beda-venerabilis` | latin |
| 24 | `ephraem-syrus` | Ephrem the Syrian | 306–373 | 1920 | benedict-xv | `mr:0609-ephraem` | syriac |
| 25 | `petrus-canisius` | Peter Canisius | 1521–1597 | 1925 | pius-xi | `mr:1221-petrus-canisius` | latin |
| 26 | `ioannes-a-cruce` | John of the Cross | 1542–1591 | 1926 | pius-xi | `mr:1214-ioannes-a-cruce` | latin |
| 27 | `albertus-magnus` | Albert the Great | 1200–1280 | 1931 | pius-xi | `mr:1115-albertus-magnus` | latin |
| 28 | `robertus-bellarminus` | Robert Bellarmine | 1542–1621 | 1931 | pius-xi | `mr:0917-robertus-bellarmino` * | latin |
| 29 | `antonius-patavinus` | Anthony of Padua | 1195–1231 | 1946 | pius-xii | `mr:0613-antonius` | latin |
| 30 | `laurentius-de-brundusio` | Lawrence of Brindisi | 1559–1619 | 1959 | john-xxiii | `mr:0721-laurentius-de-brundusio` | latin |
| 31 | `catharina-senensis` | Catherine of Siena | 1347–1380 | 1970 | paul-vi | `mr:0429-catharina-senensis` | latin |
| 32 | `teresia-a-iesu` | Teresa of Ávila | 1515–1582 | 1970 | paul-vi | `mr:1015-teresia-a-iesu` | latin |
| 33 | `teresia-a-iesu-infante` | Thérèse of Lisieux | 1873–1897 | 1997 | john-paul-ii | `mr:1001-teresia-a-iesu-infante` | latin |
| 34 | `hildegardis-bingensis` | Hildegard of Bingen | 1098–1179 | 2012 | benedict-xvi | `mr:0917-hildegardis` | latin |
| 35 | `ioannes-de-avila` | John of Ávila | 1500–1569 | 2012 | benedict-xvi | `mr:0510-ioannes-de-abula` * | latin |
| 36 | `gregorius-narecensis` | Gregory of Narek | 951–1003 | 2015 | francis-i | `null` | armenian |
| 37 | `irenaeus-lugdunensis` | Irenaeus of Lyon | 130–202 | 2022 | francis-i | `mr:0628-irenaeus` | greek |
| 38 | `ioannes-henricus-newman` | John Henry Newman | 1801–1890 | 2025 | leo-xiv | `null` | latin |

**Legend.** ‡ Basil and Gregory Nazianzen share one joint memorial eulogy (2
Jan). · \* the `mr_ref` stem differs from the `doct:` slug for a reason *beyond*
the systematic Latin epithet of rule 1 — a nominative normalization (rule 4), a
spelling to reconcile against the decree (rule 2), or a Doctor-vs-pope frame
(rule 5); in every such case the `mr_ref` value is CRMEDR's id **as it stands**.
That most `doct:` slugs are fuller than their bare CRMEDR counterpart (rule 1) is
the systematic norm, not an exception, and is left unmarked.

The `declared_by` popes and the exact Latin name-forms in this table are the
registry's best compilation and are **verified against the declaration decrees**
during implementation; life-dates for antiquity are approximate and flagged in
`note`.

## 4. Repository layout and tooling

```
cdoctdr/
  README.md                        — what/why, ID scheme summary, contents, sources
  LICENSE                          — Apache-2.0
  .gitignore
  data/doctors.json                — hand-authored source of truth (38 entries)
  registry/doctors.md              — generated human-readable table
  docs/schema-proposal.md          — full grammar, derivation & normalization rules, open questions
  docs/superpowers/specs/          — this design document
  scripts/generate_registry.py     — renders registry/doctors.md from data/doctors.json
  scripts/test_generate_registry.py
```

`data/doctors.json` is authored by hand; `registry/doctors.md` is **generated**
from it by `scripts/generate_registry.py` (stdlib-only, byte-deterministic), which
is the **sole writer** of the table so it cannot silently drift. The generator
**validates as it renders** and fails loudly on any violation:

- `id` unique and matching `^doct:[a-z]+(-[a-z]+)*$`;
- `number` an exact contiguous 1–38 in declaration order, tiebroken by death year;
- `tradition` drawn only from the controlled vocabulary;
- `declared_by` a well-formed `rp:` identifier; `mr_ref` null or a well-formed
  `mr:` identifier;
- `honorific_la` present iff `honorific_en` present.

Following the COECDR portability precedent, cross-reference existence checks are
**soft**: when a sibling `../crpdr` checkout is present the generator verifies
each `declared_by` resolves, and when `../crmedr` is present it verifies each
non-null `mr_ref` resolves; absent the checkout, those checks skip rather than
hard-fail, so a standalone clone still builds. Tests:
`python3 -m unittest discover -s scripts`.

## 5. Open questions (recorded in `docs/schema-proposal.md`, non-blocking)

1. **CRMEDR spelling normalizations.** Several `mr_ref` targets carry non-classical
   or inflected forms — `leo-i` (regnal, not doctoral), `robertus-bellarmino`
   (Italianate for `bellarminus`), `ioannes-de-abula` (for `avila`),
   `ioannes-damasceni` / `ioannes-chrysostomi` (genitive). CDOCTDR uses the
   classical/nominative/doctoral form in `doct:` and points `mr_ref` at CRMEDR's
   id as it stands. Whether to additionally open **CRMEDR normalization issues**
   (CRMEDR has a deprecated-id-correction mechanism) so the two registries
   converge is a CETF question, not a blocker.
2. **Decree verification.** The authoritative Latin name-form, the proclaiming
   pope, the year, and any conferred honorific title must be checked against each
   Doctor's **declaration decree** (papal bull / apostolic letter). This is a
   data-authoring task of the implementation plan; the values in §3.5 are the
   working compilation pending that verification (Bellarmine's `-us` vs `-o` and
   Liguori's spelling especially).
3. **Irenaeus `tradition`.** `greek` (language, patristic lineage) vs `latin`
   (see of Lyon). Defaulted to `greek` with the East–West bridge in `note`.
4. **`cdcf_person` cross-reference.** Deliberately omitted from the seed; recorded
   as a future field once a person namespace is settled (as in CRPDR's
   `cdcf_person` and COECDR's `cdcf:` open question), since Doctors are saint-persons.
5. **`honorific_*` sourcing.** Traditional Latin honorifics are not in the popular
   sources and will be authored from general knowledge and the decrees, `null`
   where no traditional title exists (several modern Doctors). A committee pass is
   invited.

All identifiers and fields are **drafts pending CETF review.**
