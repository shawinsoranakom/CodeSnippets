def test_inline_model_with_to_field(self):
        """
        #13794 --- An inline model with a to_field of a formset with instance
        has working relations.
        """
        FormSet = inlineformset_factory(User, UserSite, exclude=("is_superuser",))

        user = User.objects.create(username="guido", serial=1337)
        UserSite.objects.create(user=user, data=10)
        formset = FormSet(instance=user)

        # Testing the inline model's relation
        self.assertEqual(formset[0].instance.user_id, "guido")