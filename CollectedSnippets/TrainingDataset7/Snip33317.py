def test_bad_placeholder_2(self):
        """
        Error in translation file should not crash template rendering (#18393).
        (%(person) misses a 's' in fr.po, causing the string formatting to
        fail) .
        """
        with translation.override("fr"):
            t = Template(
                "{% load i18n %}{% blocktranslate %}My other name is {{ person }}."
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context({"person": "James"}))
            self.assertEqual(rendered, "My other name is James.")