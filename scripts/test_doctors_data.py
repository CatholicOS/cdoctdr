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
