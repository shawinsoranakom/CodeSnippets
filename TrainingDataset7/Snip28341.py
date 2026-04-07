def test_exclude_fields_with_string(self):
        msg = (
            "CategoryForm.Meta.exclude cannot be a string. Did you mean to type: "
            "('url',)?"
        )
        with self.assertRaisesMessage(TypeError, msg):

            class CategoryForm(forms.ModelForm):
                class Meta:
                    model = Category
                    exclude = "url"