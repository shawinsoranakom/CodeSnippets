def test_truncatechars01(self):
        output = self.engine.render_to_string(
            "truncatechars01", {"a": "Testing, testing"}
        )
        self.assertEqual(output, "Te…")