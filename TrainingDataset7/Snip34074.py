def test_widthratio20(self):
        output = self.engine.render_to_string(
            "widthratio20", {"a": float("inf"), "b": float("inf")}
        )
        self.assertEqual(output, "")