import unittest

import generate_registry as gen


def sample_doc():
    return {
        "doctor_count": 2,
        "id_scheme": "doct:<latin-lemma>",
        "entries": [
            {
                "number": 1, "id": "doct:thomas-de-aquino",
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
            {
                "number": 2, "id": "doct:athanasius-alexandrinus",
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
        ],
    }


class TestValidate(unittest.TestCase):
    def setUp(self):
        self._orig = gen.DOCTOR_COUNT
        gen.DOCTOR_COUNT = 2
        self.addCleanup(setattr, gen, "DOCTOR_COUNT", self._orig)
        self.doc = sample_doc()

    def test_accepts_good_doc(self):
        gen.validate(self.doc)  # must not raise

    def test_rejects_wrong_count(self):
        self.doc["doctor_count"] = 3
        with self.assertRaises(ValueError):
            gen.validate(self.doc)

    def test_rejects_wrong_total_count(self):
        # Remove one entry so len(entries) becomes 1, violating DOCTOR_COUNT check
        self.doc["entries"].pop()
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
        self._orig = gen.DOCTOR_COUNT
        gen.DOCTOR_COUNT = 2
        self.addCleanup(setattr, gen, "DOCTOR_COUNT", self._orig)
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


class TestConstants(unittest.TestCase):
    def test_doctor_count_is_38(self):
        self.assertEqual(gen.DOCTOR_COUNT, 38)


if __name__ == "__main__":
    unittest.main()
