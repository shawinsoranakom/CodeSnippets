def test_join03(self):
        output = self.engine.render_to_string("join03", {"a": ["alpha", "beta & me"]})
        self.assertEqual(output, "alpha &amp; beta &amp; me")