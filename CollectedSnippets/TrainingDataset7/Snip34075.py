def test_widthratio21(self):
        output = self.engine.render_to_string(
            "widthratio21", {"a": float("inf"), "b": 2}
        )
        self.assertEqual(output, "")