def test_unit_att_name(self):
        "Testing the `unit_attname` class method"
        unit_tuple = [
            ("Yard", "yd"),
            ("Nautical Mile", "nm"),
            ("German legal metre", "german_m"),
            ("Indian yard", "indian_yd"),
            ("Chain (Sears)", "chain_sears"),
            ("Chain", "chain"),
            ("Furrow Long", "furlong"),
        ]
        for nm, att in unit_tuple:
            with self.subTest(nm=nm):
                self.assertEqual(att, D.unit_attname(nm))