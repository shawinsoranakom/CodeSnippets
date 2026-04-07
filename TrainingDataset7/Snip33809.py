def test_include10(self):
        output = self.engine.render_to_string("include10", {"first": "1"})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID --- INVALID")
        else:
            self.assertEqual(output, " --- ")