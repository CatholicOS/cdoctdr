# CDOCTDR Schema Proposal

**Status:** Draft, pending CETF review.
**Registry:** Common DOCTors of the Church Data Repository (`CatholicOS/cdoctdr`).

## 1. Identifier grammar

```abnf
doctor-id    = "doct:" lemma
lemma        = lowercase *( lowercase / "-" ) lowercase
lowercase    = %x61-7A                        ; a-z
```

`^doct:[a-z]+(-[a-z]+)*$`

Examples: `doct:thomas-de-aquino`, `doct:ioannes-a-cruce`, `doct:catharina-senensis`,
`doct:beda-venerabilis`.

### 1.1 Derivation rules

1. **Full conventional appellation.** Every slug carries the Doctor's
   conventional distinguishing epithet — a toponym (`hipponensis`, `senensis`,
   `bingensis`, `pictaviensis`, `lugdunensis`), a cognomen (`magnus`,
   `chrysologus`, `chrysostomus`, `venerabilis`), or a religious name
   (`a-iesu`, `a-cruce`). There are no bare mononyms: Augustine of Hippo is
   `doct:augustinus-hipponensis`, not `doct:augustinus`; Ambrose is
   `doct:ambrosius-mediolanensis`. This maximises resolution and future-proofs
   the namespace against a later Doctor of the same base name.
2. **Latin form from the declaration decree.** Where the Latin proclamation
   decree fixes a name-form, that form governs. The registry uses the
   classical `doct:robertus-bellarminus` and `doct:leo-magnus`, verified
   against the decrees during data authoring.
3. **CRMEDR alignment, with promotion for global uniqueness.** Where CRMEDR
   already carries the same saint, the registry reuses its lemma. But CRMEDR
   IDs are date-scoped (`mr:MMDD-slug`), so CRMEDR can keep two homonyms apart
   by their calendar day; `doct:` IDs are not date-scoped, so any lemma not
   globally unique among the 38 Doctors is promoted with its epithet. Forced
   case: the two Cyrils — `doct:cyrillus-hierosolymitanus` and
   `doct:cyrillus-alexandrinus` (CRMEDR: bare `cyrillus` on 03-18 and 06-27).
4. **Nominative normalization.** Where a CRMEDR eulogy text carries a
   per-entry grammatical inflection, the `doct:` slug is the clean nominative:
   `doct:ioannes-chrysostomus` (CRMEDR text *…chrysostomi*),
   `doct:ioannes-damascenus` (CRMEDR text *…damasceni*). The `mr_ref` field
   still points at CRMEDR's actual id, so the hard link is preserved.
5. **Doctor-frame, not pope-frame.** Where CRMEDR identifies a saint-pope by
   regnal ordinal (`mr:1110-leo-i`), CDOCTDR identifies the same person *in
   his capacity as a Doctor* by his doctoral cognomen: `doct:leo-magnus`. The
   `mr_ref` bridges the two frames.

## 2. Data fields

Each entry in `data/doctors.json`:

| field | type | meaning |
| --- | --- | --- |
| `number` | int 1–38 | position in the declaration sequence (§3) |
| `id` | string | the `doct:` canonical identifier |
| `name` | string | the Doctor's common English name ("Augustine of Hippo") |
| `label_en` | string | English display label (may equal `name`) |
| `label_la` | string | Latin nominative display form ("Augustinus Hipponensis") — the provenance of the slug |
| `aliases` | list[string] | alternative names (a bare honorific such as "Doctor Angelicus" is *not* an alias — see `honorific_*`) |
| `birth_year` | int \| null | year of birth (approximate for antiquity, flagged in `note`) |
| `death_year` | int \| null | year of death |
| `century` | int | century of death (the era to which the Doctor belongs) |
| `birthplace` | string \| null | place of birth |
| `birth_country` | string \| null | ISO 3166-1 alpha-2 of the modern country of that place |
| `tradition` | string | ecclesial/cultural tradition, controlled vocabulary `latin` / `greek` / `syriac` / `armenian` |
| `honorific_la` | string \| null | traditional Latin honorific ("Doctor Angelicus", "Doctor Gratiae"); null where no traditional title is attested |
| `honorific_en` | string \| null | English form of the honorific ("Angelic Doctor", "Doctor of Grace") |
| `declared_year` | int | year proclaimed a Doctor of the Church |
| `declared_by` | string | CRPDR `rp:` cross-reference to the proclaiming pope |
| `mr_ref` | string \| null | CRMEDR `mr:` cross-reference to the Doctor's memorial eulogy; null if the saint is absent from the *editio typica altera 2004* |
| `significance` | string | brief, original-wording summary of the Doctor's doctrinal contribution |
| `note` | string \| null | disambiguation or context (approximate dates, East–West position, decree particulars) |

Top-level metadata mirrors the sibling registries: a `$comment` (draft-status
notice), `id_scheme`, a `sources` object (background references, explicitly
marked non-authoritative), and `doctor_count` (38).

### 2.1 The `tradition` vocabulary

A single controlled value per Doctor, surfacing the non-Latin Doctors:

| value | Doctors | count |
| --- | --- | --- |
| `latin` | the Western Doctors (Ambrose … Newman) | 28 |
| `greek` | Athanasius, Basil, Gregory of Nazianzus, John Chrysostom, the two Cyrils, John Damascene (and, provisionally, Irenaeus) | 7–8 |
| `syriac` | Ephrem | 1 |
| `armenian` | Gregory of Narek | 1 |

Finer nuance (Antiochene vs Alexandrine formation, a Doctor who wrote in Greek
but served a Western see) is carried in prose (`note` / `significance`), never
multiplied into the enum. See §4, open question 3, for the one open
assignment (Irenaeus).

## 3. Ordering

Entries are ordered by **`declared_year`**, with a deterministic within-year
tiebreak by **`death_year`** (earliest first). This resolves the six years in
which more than one Doctor was proclaimed (1298 ×4, 1568 ×4, 1883 ×2, 1931 ×2,
1970 ×2, 2012 ×2) and reproduces the conventional listings. `number` is the
resulting 1–38 declaration-sequence position; there is no official Holy See
ordinal, so `number` is the registry's own presentation order, **not a
magisterial rank**.

## 4. Open questions

1. **CRMEDR Latin-form normalizations.** The `doct:` slug follows the
   declaration decree's Latin, which in several cases diverges from CRMEDR's
   Italianate or variant forms: `robertus-bellarminus` vs CRMEDR
   `robertus-bellarmino`; `alphonsus-maria-de-ligorio` vs CRMEDR's
   `alfonsus-maria-de-ligorio`; `ioannes-de-avila` vs CRMEDR
   `ioannes-de-abula`; and the nominative normalizations
   `ioannes-chrysostomus` / `ioannes-damascenus` against CRMEDR's genitive
   eulogy forms (*chrysostomi*, *damasceni*). In every case `mr_ref` points at
   CRMEDR's id **as it stands**. Whether to open CRMEDR normalization issues
   (CRMEDR has a deprecated-id-correction mechanism) so the two registries
   converge is a CETF decision, not a blocker.
2. **Decree verification.** Largely complete; the remainder is open. Hilary of
   Poitiers' 1851 declaration under Pius IX is confirmed. The roughly two
   dozen Doctors left with `honorific_la` / `honorific_en` both null — no
   traditional Latin honorific was found attested for them during this
   pass — await a title decision from the committee rather than a further
   compilation effort.
3. **Honorific completion and contested titles.** Anselm of Canterbury has two
   co-attested titles: *Doctor Magnificus* (the "Magnificent Doctor", used in
   this seed) and *Doctor Marianus* ("Marian Doctor", a title he shares with
   Bl. John Duns Scotus). Thérèse of Lisieux's honorific is a modern (1997)
   epithet with no cleanly-attested Latin honorific form; the seed leaves it
   `null` rather than record an unqualified "Doctor of Love" — any recorded
   form must be an attested *qualified* one (e.g. "Doctor of Divine Love").
4. **Irenaeus `tradition`.** `greek` (language and patristic lineage, the
   current default) vs `latin` (his see of Lyon). The East–West bridge is
   recorded in his `note` and is the ground of his honorific *Doctor
   unitatis*.
5. **`cdcf_person` cross-reference.** Deliberately omitted from the seed;
   recorded as a future field once a person namespace is settled (as in
   CRPDR's `cdcf_person` and COECDR's `cdcf:` open question), since Doctors
   are saint-persons.

All identifiers and fields are **drafts pending CETF review.**
