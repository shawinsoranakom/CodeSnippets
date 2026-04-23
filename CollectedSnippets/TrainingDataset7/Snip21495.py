def test_hash(self):
        d = {Value("name"): "Bob"}
        self.assertIn(Value("name"), d)
        self.assertEqual(d[Value("name")], "Bob")