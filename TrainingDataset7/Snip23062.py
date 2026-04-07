def test_non_ascii_choices(self):
        class SomeForm(Form):
            somechoice = ChoiceField(
                choices=(("\xc5", "En tied\xe4"), ("\xf8", "Mies"), ("\xdf", "Nainen")),
                widget=RadioSelect(),
                label="\xc5\xf8\xdf",
            )

        f = SomeForm()
        self.assertHTMLEqual(
            f.as_p(),
            "<p><label>\xc5\xf8\xdf:</label>"
            '<div id="id_somechoice">\n'
            '<div><label for="id_somechoice_0">'
            '<input type="radio" id="id_somechoice_0" value="\xc5" name="somechoice" '
            "required> En tied\xe4</label></div>\n"
            '<div><label for="id_somechoice_1">'
            '<input type="radio" id="id_somechoice_1" value="\xf8" name="somechoice" '
            'required> Mies</label></div>\n<div><label for="id_somechoice_2">'
            '<input type="radio" id="id_somechoice_2" value="\xdf" name="somechoice" '
            "required> Nainen</label></div>\n</div></p>",
        )

        # Translated error messages
        with translation.override("ru"):
            f = SomeForm({})
            self.assertHTMLEqual(
                f.as_p(),
                '<ul class="errorlist" id="id_somechoice_error"><li>'
                "\u041e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c"
                "\u043d\u043e\u0435 \u043f\u043e\u043b\u0435.</li></ul>\n"
                "<p><label>\xc5\xf8\xdf:</label>"
                ' <div id="id_somechoice">\n<div><label for="id_somechoice_0">'
                '<input type="radio" id="id_somechoice_0" value="\xc5" '
                'name="somechoice" aria-invalid="true" required>'
                "En tied\xe4</label></div>\n"
                '<div><label for="id_somechoice_1">'
                '<input type="radio" id="id_somechoice_1" value="\xf8" '
                'name="somechoice" aria-invalid="true" required>'
                "Mies</label></div>\n<div>"
                '<label for="id_somechoice_2">'
                '<input type="radio" id="id_somechoice_2" value="\xdf" '
                'name="somechoice" aria-invalid="true" required>'
                "Nainen</label></div>\n</div></p>",
            )