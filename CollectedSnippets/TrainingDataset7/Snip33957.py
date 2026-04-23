def test_resetcycle06(self):
        output = self.engine.render_to_string("resetcycle06", {"test": list(range(5))})
        self.assertEqual(output, "ab-c-a-b-c-")