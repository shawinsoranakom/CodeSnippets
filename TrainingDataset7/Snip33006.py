def test_linenumbers01(self):
        output = self.engine.render_to_string(
            "linenumbers01",
            {"a": "one\n<two>\nthree", "b": mark_safe("one\n&lt;two&gt;\nthree")},
        )
        self.assertEqual(
            output, "1. one\n2. &lt;two&gt;\n3. three 1. one\n2. &lt;two&gt;\n3. three"
        )