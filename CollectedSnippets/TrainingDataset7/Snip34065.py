def test_widthratio13a(self):
        output = self.engine.render_to_string(
            "widthratio13a", {"a": 0, "c": 100, "b": "b"}
        )
        self.assertEqual(output, "")