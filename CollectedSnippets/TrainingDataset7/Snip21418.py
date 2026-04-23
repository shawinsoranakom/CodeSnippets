def test_hash(self):
        d = {F("name"): "Bob"}
        self.assertIn(F("name"), d)
        self.assertEqual(d[F("name")], "Bob")