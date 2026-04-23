def test_legacywith01(self):
        output = self.engine.render_to_string("legacywith01", {"dict": {"key": 50}})
        self.assertEqual(output, "50")