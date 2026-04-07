def test_bad_placeholder_1(self):
        """
        Error in translation file should not crash template rendering (#16516).
        (%(person)s is translated as %(personne)s in fr.po).
        """
        with translation.override("fr"):
            t = Template(
                "{% load i18n %}{% blocktranslate %}My name is {{ person }}."
                "{% endblocktranslate %}"
            )
            rendered = t.render(Context({"person": "James"}))
            self.assertEqual(rendered, "My name is James.")