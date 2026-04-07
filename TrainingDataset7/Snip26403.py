def test_get_prefetch_querysets_invalid_querysets_length(self):
        City.objects.create(name="Chicago")
        cities = City.objects.all()
        msg = (
            "querysets argument of get_prefetch_querysets() should have a length of 1."
        )
        with self.assertRaisesMessage(ValueError, msg):
            City.country.get_prefetch_querysets(
                instances=cities,
                querysets=[Country.objects.all(), Country.objects.all()],
            )