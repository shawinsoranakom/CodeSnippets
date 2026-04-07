def test_inline_model_with_primary_to_field(self):
        """An inline model with a OneToOneField with to_field & primary key."""
        FormSet = inlineformset_factory(
            User, UserPreferences, exclude=("is_superuser",)
        )
        user = User.objects.create(username="guido", serial=1337)
        UserPreferences.objects.create(user=user, favorite_number=10)
        formset = FormSet(instance=user)
        self.assertEqual(formset[0].fields["user"].initial, "guido")