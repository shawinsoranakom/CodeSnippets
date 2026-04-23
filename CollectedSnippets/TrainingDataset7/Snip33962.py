def test_resetcycle11(self):
        output = self.engine.render_to_string("resetcycle11", {"test": list(range(5))})
        self.assertEqual(output, "XaYbXcYaZb")