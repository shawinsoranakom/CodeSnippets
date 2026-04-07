def test_model_multiple_choice_field_22745(self):
        """
        #22745 -- Make sure that ModelMultipleChoiceField with
        CheckboxSelectMultiple widget doesn't produce unnecessary db queries
        when accessing its BoundField's attrs.
        """

        class ModelMultipleChoiceForm(forms.Form):
            categories = forms.ModelMultipleChoiceField(
                Category.objects.all(), widget=forms.CheckboxSelectMultiple
            )

        form = ModelMultipleChoiceForm()
        field = form["categories"]  # BoundField
        template = Template("{{ field.name }}{{ field }}{{ field.help_text }}")
        with self.assertNumQueries(1):
            template.render(Context({"field": field}))