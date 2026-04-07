def test_include14(self):
        output = self.engine.render_to_string("include14", {"var1": "&"})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "& --- INVALID")
        else:
            self.assertEqual(output, "& --- ")