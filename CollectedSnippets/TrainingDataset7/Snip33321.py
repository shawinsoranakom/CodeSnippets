def test_multiple_locale_deactivate_btrans(self):
        with translation.override("de", deactivate=True):
            t = self.get_template(
                "{% load i18n %}{% blocktranslate %}No{% endblocktranslate %}"
            )
        with translation.override("nl"):
            self.assertEqual(t.render(Context({})), "Nee")