def test_custom_form_with_non_required_password(self):
        class CustomUserCreationForm(BaseUserCreationForm):
            password1 = forms.CharField(required=False)
            password2 = forms.CharField(required=False)
            another_field = forms.CharField(required=True)

        data = {
            "username": "testclientnew",
            "another_field": "Content",
        }
        form = CustomUserCreationForm(data)
        self.assertIs(form.is_valid(), True, form.errors)