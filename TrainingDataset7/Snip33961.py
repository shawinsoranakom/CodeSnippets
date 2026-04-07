def test_resetcycle10(self):
        output = self.engine.render_to_string("resetcycle10", {"test": list(range(5))})
        self.assertEqual(output, "XaYbZaXbYc")