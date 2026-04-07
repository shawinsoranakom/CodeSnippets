def test_label(self):
        """
        CheckboxSelectMultiple doesn't contain 'for="field_0"' in the <label>
        because clicking that would toggle the first checkbox.
        """

        class TestForm(forms.Form):
            f = forms.MultipleChoiceField(widget=CheckboxSelectMultiple)

        bound_field = TestForm()["f"]
        self.assertEqual(bound_field.field.widget.id_for_label("id"), "")
        self.assertEqual(bound_field.label_tag(), "<label>F:</label>")
        self.assertEqual(bound_field.legend_tag(), "<legend>F:</legend>")