def test_get_prefetch_querysets_reverse_invalid_querysets_length(self):
        usa = Country.objects.create(name="United States")
        City.objects.create(name="Chicago")
        countries = Country.objects.all()
        msg = (
            "querysets argument of get_prefetch_querysets() should have a length of 1."
        )
        with self.assertRaisesMessage(ValueError, msg):
            usa.cities.get_prefetch_querysets(
                instances=countries,
                querysets=[City.objects.all(), City.objects.all()],
            )