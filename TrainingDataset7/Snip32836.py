def test_chaining03(self):
        output = self.engine.render_to_string(
            "chaining03", {"a": "a < b", "b": mark_safe("a < b")}
        )
        self.assertEqual(output, "A &lt; .A < ")