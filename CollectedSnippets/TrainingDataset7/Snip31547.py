def test_model_proxy_of_argument_raises_error_proxy_field_in_choices(self):
        msg = (
            "Invalid field name(s) given in select_for_update(of=(...)): "
            "name. Only relational fields followed in the query are allowed. "
            "Choices are: self, country, country__entity_ptr."
        )
        with self.assertRaisesMessage(FieldError, msg):
            with transaction.atomic():
                CityCountryProxy.objects.select_related(
                    "country",
                ).select_for_update(of=("name",)).get()