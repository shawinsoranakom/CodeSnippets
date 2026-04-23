def test_model_inheritance_of_argument_raises_error_ptr_in_choices(self):
        msg = (
            "Invalid field name(s) given in select_for_update(of=(...)): "
            "name. Only relational fields followed in the query are allowed. "
            "Choices are: self, %s."
        )
        with self.assertRaisesMessage(
            FieldError,
            msg % "country, country__country_ptr, country__country_ptr__entity_ptr",
        ):
            with transaction.atomic():
                EUCity.objects.select_related(
                    "country",
                ).select_for_update(of=("name",)).get()
        with self.assertRaisesMessage(
            FieldError, msg % "country_ptr, country_ptr__entity_ptr"
        ):
            with transaction.atomic():
                EUCountry.objects.select_for_update(of=("name",)).get()