def test_no_translations_deactivate_translations(self):
        """
        When the Command handle method is decorated with @no_translations,
        translations are deactivated inside the command.
        """
        current_locale = translation.get_language()
        with translation.override("pl"):
            result = management.call_command("no_translations")
            self.assertIsNone(result)
        self.assertEqual(translation.get_language(), current_locale)