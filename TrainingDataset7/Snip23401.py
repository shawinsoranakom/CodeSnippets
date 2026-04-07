def test_fieldset_with_unhidden_field(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            hidden_field = SplitDateTimeField(widget=self.widget)
            unhidden_field = SplitDateTimeField()

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, True)
        self.assertHTMLEqual(
            "<div><fieldset><legend>Unhidden field:</legend>"
            '<input type="text" name="unhidden_field_0" required '
            'id="id_unhidden_field_0"><input type="text" '
            'name="unhidden_field_1" required id="id_unhidden_field_1">'
            '</fieldset><input type="hidden" name="hidden_field_0" '
            'id="id_hidden_field_0"><input type="hidden" '
            'name="hidden_field_1" id="id_hidden_field_1"></div>',
            form.render(),
        )