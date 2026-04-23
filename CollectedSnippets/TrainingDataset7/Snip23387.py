def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = ChoiceField(
                widget=self.widget, choices=self.beatles, required=False
            )

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, False)
        self.assertHTMLEqual(
            '<div><label for="id_field">Field:</label>'
            '<select multiple name="field" id="id_field">'
            '<option value="J">John</option>  <option value="P">Paul</option>'
            '<option value="G">George</option><option value="R">Ringo'
            "</option></select></div>",
            form.render(),
        )