def test_i18n30(self):
        output = self.engine.render_to_string("i18n30", {"langcodes": ["it", "no"]})
        self.assertEqual(
            output, "it: Italian/italiano bidi=False; no: Norwegian/norsk bidi=False; "
        )