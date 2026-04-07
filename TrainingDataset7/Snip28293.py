def test_no_extra_query_when_accessing_attrs(self):
        """
        ModelChoiceField with RadioSelect widget doesn't produce unnecessary
        db queries when accessing its BoundField's attrs.
        """

        class ModelChoiceForm(forms.Form):
            category = forms.ModelChoiceField(
                Category.objects.all(), widget=forms.RadioSelect
            )

        form = ModelChoiceForm()
        field = form["category"]  # BoundField
        template = Template("{{ field.name }}{{ field }}{{ field.help_text }}")
        with self.assertNumQueries(1):
            template.render(Context({"field": field}))