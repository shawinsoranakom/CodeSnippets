def test_single_locale_activation(self):
        """
        Simple baseline behavior with one locale for all the supported i18n
        constructs.
        """
        with translation.override("fr"):
            self.assertEqual(
                self.get_template(
                    "{% load i18n %}{% blocktranslate %}Yes{% endblocktranslate %}"
                ).render(Context({})),
                "Oui",
            )