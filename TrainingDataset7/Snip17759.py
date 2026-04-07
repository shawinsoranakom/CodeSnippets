def test_custom_form_saves_many_to_many_field(self):
        class CustomUserCreationForm(BaseUserCreationForm):
            class Meta(BaseUserCreationForm.Meta):
                model = CustomUserWithM2M
                fields = UserCreationForm.Meta.fields + ("orgs",)

        organization = Organization.objects.create(name="organization 1")

        data = {
            "username": "testclient@example.com",
            "password1": "testclient",
            "password2": "testclient",
            "orgs": [str(organization.pk)],
        }
        form = CustomUserCreationForm(data)
        self.assertIs(form.is_valid(), True)
        user = form.save(commit=True)
        self.assertSequenceEqual(user.orgs.all(), [organization])