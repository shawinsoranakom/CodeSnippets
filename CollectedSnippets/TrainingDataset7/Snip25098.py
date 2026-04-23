def test_iter_format_modules(self):
        """
        Tests the iter_format_modules function.
        """
        # Importing some format modules so that we can compare the returned
        # modules with these expected modules
        default_mod = import_module("django.conf.locale.de.formats")
        test_mod = import_module("i18n.other.locale.de.formats")
        test_mod2 = import_module("i18n.other2.locale.de.formats")

        with translation.override("de-at", deactivate=True):
            # Should return the correct default module when no setting is set
            self.assertEqual(list(iter_format_modules("de")), [default_mod])

            # When the setting is a string, should return the given module and
            # the default module
            self.assertEqual(
                list(iter_format_modules("de", "i18n.other.locale")),
                [test_mod, default_mod],
            )

            # When setting is a list of strings, should return the given
            # modules and the default module
            self.assertEqual(
                list(
                    iter_format_modules(
                        "de", ["i18n.other.locale", "i18n.other2.locale"]
                    )
                ),
                [test_mod, test_mod2, default_mod],
            )