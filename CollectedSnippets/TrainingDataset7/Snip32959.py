def test_join01(self):
        output = self.engine.render_to_string("join01", {"a": ["alpha", "beta & me"]})
        self.assertEqual(output, "alpha, beta &amp; me")