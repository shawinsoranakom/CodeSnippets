def test_inherited_unique_field_with_form(self):
        """
        A model which has different primary key for the parent model passes
        unique field checking correctly (#17615).
        """

        class ProfileForm(forms.ModelForm):
            class Meta:
                model = Profile
                fields = "__all__"

        User.objects.create(username="user_only")
        p = Profile.objects.create(username="user_with_profile")
        form = ProfileForm(
            {"username": "user_with_profile", "extra": "hello"}, instance=p
        )
        self.assertTrue(form.is_valid())