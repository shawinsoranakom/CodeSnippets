def test_limit_fields_with_string(self):
        msg = (
            "CategoryForm.Meta.fields cannot be a string. Did you mean to type: "
            "('url',)?"
        )
        with self.assertRaisesMessage(TypeError, msg):

            class CategoryForm(forms.ModelForm):
                class Meta:
                    model = Category
                    fields = "url"