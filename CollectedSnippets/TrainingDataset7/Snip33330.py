def test_i18n38_2(self):
        with translation.override("cs"):
            output = self.engine.render_to_string(
                "i18n38_2", {"langcodes": ["it", "fr"]}
            )
        self.assertEqual(
            output,
            "it: Italian/italiano/italsky bidi=False; "
            "fr: French/français/francouzsky bidi=False; ",
        )