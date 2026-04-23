def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = SplitDateTimeField(widget=self.widget)

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, True)
        self.assertHTMLEqual(
            '<input type="hidden" name="field_0" id="id_field_0">'
            '<input type="hidden" name="field_1" id="id_field_1">',
            form.render(),
        )