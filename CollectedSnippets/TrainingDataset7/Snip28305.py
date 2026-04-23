def test_num_queries(self):
        """
        Widgets that render multiple subwidgets shouldn't make more than one
        database query.
        """
        categories = Category.objects.all()

        class CategoriesForm(forms.Form):
            radio = forms.ModelChoiceField(
                queryset=categories, widget=forms.RadioSelect
            )
            checkbox = forms.ModelMultipleChoiceField(
                queryset=categories, widget=forms.CheckboxSelectMultiple
            )

        template = Template(
            "{% for widget in form.checkbox %}{{ widget }}{% endfor %}"
            "{% for widget in form.radio %}{{ widget }}{% endfor %}"
        )
        with self.assertNumQueries(2):
            template.render(Context({"form": CategoriesForm()}))