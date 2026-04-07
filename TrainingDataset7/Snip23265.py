def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = FileField(widget=self.widget)

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, False)
        self.assertHTMLEqual(
            '<div><label for="id_field">Field:</label><input id="id_field" '
            'name="field" required type="file"></div>',
            form.render(),
        )