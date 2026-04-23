def test_model_form_clean_applies_to_model(self):
        """
        Regression test for #12960. Make sure the cleaned_data returned from
        ModelForm.clean() is applied to the model instance.
        """

        class CategoryForm(forms.ModelForm):
            class Meta:
                model = Category
                fields = "__all__"

            def clean(self):
                self.cleaned_data["name"] = self.cleaned_data["name"].upper()
                return self.cleaned_data

        data = {"name": "Test", "slug": "test", "url": "/test"}
        form = CategoryForm(data)
        category = form.save()
        self.assertEqual(category.name, "TEST")