def test_include11(self):
        output = self.engine.render_to_string("include11", {"first": "1"})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID --- 2")
        else:
            self.assertEqual(output, " --- 2")