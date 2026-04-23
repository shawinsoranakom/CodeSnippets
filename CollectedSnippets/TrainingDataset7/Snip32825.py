def test_capfirst02(self):
        output = self.engine.render_to_string(
            "capfirst02", {"a": "fred>", "b": mark_safe("fred&gt;")}
        )
        self.assertEqual(output, "Fred&gt; Fred&gt;")