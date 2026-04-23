def test_truncatechars02(self):
        output = self.engine.render_to_string("truncatechars02", {"a": "Testing"})
        self.assertEqual(output, "Testing")