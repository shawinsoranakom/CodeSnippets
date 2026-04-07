def test_join08(self):
        output = self.engine.render_to_string(
            "join08", {"a": ["Alpha", "Beta & me"], "var": mark_safe(" & ")}
        )
        self.assertEqual(output, "alpha & beta &amp; me")