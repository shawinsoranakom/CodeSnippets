def test_chaining04(self):
        output = self.engine.render_to_string(
            "chaining04", {"a": "a < b", "b": mark_safe("a < b")}
        )
        self.assertEqual(output, "A < .A < ")