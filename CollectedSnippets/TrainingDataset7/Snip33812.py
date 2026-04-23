def test_include13(self):
        output = self.engine.render_to_string("include13", {"first": "&"})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "& --- INVALID")
        else:
            self.assertEqual(output, "& --- ")