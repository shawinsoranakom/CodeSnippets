def test_self_reference_dict(self):
        d1 = {"cat": "hat"}
        d2 = {"things": [1, 2]}

        self.assertEqual(get_hash(d1), get_hash(d1))
        self.assertNotEqual(get_hash(d1), get_hash(d2))

        # test that we can hash self-referencing dictionaries
        d2 = {"book": d1}
        self.assertNotEqual(get_hash(d2), get_hash(d1))