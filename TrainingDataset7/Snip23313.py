def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = NullBooleanField(widget=self.widget)

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, False)
        self.assertHTMLEqual(
            '<div><label for="id_field">Field:</label>'
            '<select name="field" id="id_field">'
            '<option value="unknown" selected>Unknown</option>'
            '<option value="true">Yes</option>'
            '<option value="false">No</option></select></div>',
            form.render(),
        )