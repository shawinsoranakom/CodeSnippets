def test_inline_model_with_to_field_to_rel(self):
        """
        #13794 --- An inline model with a to_field to a related field of a
        formset with instance has working relations.
        """
        FormSet = inlineformset_factory(UserProfile, ProfileNetwork, exclude=[])

        user = User.objects.create(username="guido", serial=1337, pk=1)
        self.assertEqual(user.pk, 1)
        profile = UserProfile.objects.create(user=user, about="about", pk=2)
        self.assertEqual(profile.pk, 2)
        ProfileNetwork.objects.create(profile=profile, network=10, identifier=10)
        formset = FormSet(instance=profile)

        # Testing the inline model's relation
        self.assertEqual(formset[0].instance.profile_id, 1)