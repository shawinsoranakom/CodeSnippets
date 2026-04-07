def test_i18n31(self):
        output = self.engine.render_to_string(
            "i18n31", {"langcodes": (("sl", "Slovenian"), ("fa", "Persian"))}
        )
        self.assertEqual(
            output,
            "sl: Slovenian/Sloven\u0161\u010dina bidi=False; "
            "fa: Persian/\u0641\u0627\u0631\u0633\u06cc bidi=True; ",
        )