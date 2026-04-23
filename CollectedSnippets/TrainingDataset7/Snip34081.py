def test_legacywith02(self):
        output = self.engine.render_to_string("legacywith02", {"dict": {"key": 50}})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID50-50-50INVALID")
        else:
            self.assertEqual(output, "50-50-50")