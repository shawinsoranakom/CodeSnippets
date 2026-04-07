def test_multiple_locale_btrans(self):
        with translation.override("de"):
            t = self.get_template(
                "{% load i18n %}{% blocktranslate %}No{% endblocktranslate %}"
            )
        with translation.override(self._old_language), translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")