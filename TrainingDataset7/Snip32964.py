def test_join06(self):
        output = self.engine.render_to_string(
            "join06", {"a": ["alpha", "beta & me"], "var": mark_safe(" & ")}
        )
        self.assertEqual(output, "alpha & beta &amp; me")