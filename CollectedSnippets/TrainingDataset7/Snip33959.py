def test_resetcycle08(self):
        output = self.engine.render_to_string(
            "resetcycle08", {"outer": list(range(2)), "inner": list(range(3))}
        )
        self.assertEqual(output, "abaaba")