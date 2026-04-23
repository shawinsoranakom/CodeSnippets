def test_lazy_labels(self):
        class SomeForm(Form):
            username = CharField(max_length=10, label=gettext_lazy("username"))

        f = SomeForm()
        self.assertHTMLEqual(
            f.as_p(),
            '<p><label for="id_username">username:</label>'
            '<input id="id_username" type="text" name="username" maxlength="10" '
            "required></p>",
        )

        # Translations are done at rendering time, so multi-lingual apps can
        # define forms.
        with translation.override("de"):
            self.assertHTMLEqual(
                f.as_p(),
                '<p><label for="id_username">Benutzername:</label>'
                '<input id="id_username" type="text" name="username" maxlength="10" '
                "required></p>",
            )
        with translation.override("pl"):
            self.assertHTMLEqual(
                f.as_p(),
                '<p><label for="id_username">nazwa u\u017cytkownika:</label>'
                '<input id="id_username" type="text" name="username" maxlength="10" '
                "required></p>",
            )