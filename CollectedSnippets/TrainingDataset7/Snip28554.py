def test_model_formset_with_custom_pk(self):
        # a formset for a Model that has a custom primary key that still needs
        # to be added to the formset automatically
        FormSet = modelformset_factory(
            ClassyMexicanRestaurant, fields=["tacos_are_yummy"]
        )
        self.assertEqual(
            sorted(FormSet().forms[0].fields), ["tacos_are_yummy", "the_restaurant"]
        )