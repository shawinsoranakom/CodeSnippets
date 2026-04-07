def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = ChoiceField(
                widget=self.widget, choices=self.beatles, required=False
            )

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, True)
        self.assertHTMLEqual(
            '<div><fieldset><legend>Field:</legend><div id="id_field">'
            '<div><label for="id_field_0">'
            '<input type="radio" name="field" value="J" id="id_field_0"> John'
            '</label></div><div><label for="id_field_1">'
            '<input type="radio" name="field" value="P" id="id_field_1">Paul'
            '</label></div><div><label for="id_field_2"><input type="radio" '
            'name="field" value="G" id="id_field_2"> George</label></div>'
            '<div><label for="id_field_3"><input type="radio" name="field" '
            'value="R" id="id_field_3">Ringo</label></div></div></fieldset>'
            "</div>",
            form.render(),
        )