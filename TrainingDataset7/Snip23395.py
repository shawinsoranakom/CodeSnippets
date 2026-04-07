def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = SplitDateTimeField(widget=self.widget)

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, True)
        self.assertHTMLEqual(
            '<div><fieldset><legend>Field:</legend><input type="text" '
            'name="field_0" required id="id_field_0"><input type="text" '
            'name="field_1" required id="id_field_1"></fieldset></div>',
            form.render(),
        )