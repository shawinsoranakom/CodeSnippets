def test_limit_nonexistent_field(self):
        expected_msg = "Unknown field(s) (nonexistent) specified for Category"
        with self.assertRaisesMessage(FieldError, expected_msg):

            class InvalidCategoryForm(forms.ModelForm):
                class Meta:
                    model = Category
                    fields = ["nonexistent"]