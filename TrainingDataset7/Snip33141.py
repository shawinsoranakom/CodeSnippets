def test_fail_silently_incorrect_arg(self):
        output = self.engine.render_to_string(
            "truncatechars03", {"a": "Testing, testing"}
        )
        self.assertEqual(output, "Testing, testing")