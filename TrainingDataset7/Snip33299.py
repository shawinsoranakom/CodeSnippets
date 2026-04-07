def test_i18n34_3(self):
        output = self.engine.render_to_string("i18n34_3", {"anton": "\xce\xb1"})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")