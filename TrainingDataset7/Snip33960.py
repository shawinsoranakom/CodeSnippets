def test_resetcycle09(self):
        output = self.engine.render_to_string(
            "resetcycle09", {"outer": list(range(2)), "inner": list(range(3))}
        )
        self.assertEqual(output, "aXYXbXYX")