def test_invalidstr02(self):
        output = self.engine.render_to_string("invalidstr02")
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")