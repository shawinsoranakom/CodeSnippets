def test_capfirst01(self):
        output = self.engine.render_to_string(
            "capfirst01", {"a": "fred>", "b": mark_safe("fred&gt;")}
        )
        self.assertEqual(output, "Fred> Fred&gt;")