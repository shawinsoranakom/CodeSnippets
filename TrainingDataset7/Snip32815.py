def test_addslashes01(self):
        output = self.engine.render_to_string(
            "addslashes01", {"a": "<a>'", "b": mark_safe("<a>'")}
        )
        self.assertEqual(output, r"<a>\' <a>\'")