def test_lookup_allowed_for_local_fk_fields(self):
        class Country(models.Model):
            pass

        class Place(models.Model):
            country = models.ForeignKey(Country, models.CASCADE)

        class PlaceAdmin(ModelAdmin):
            pass

        ma = PlaceAdmin(Place, self.site)

        cases = [
            ("country", "1"),
            ("country__exact", "1"),
            ("country__id", "1"),
            ("country__id__exact", "1"),
            ("country__isnull", True),
            ("country__isnull", False),
            ("country__id__isnull", False),
        ]
        for lookup, lookup_value in cases:
            with self.subTest(lookup=lookup):
                self.assertIs(ma.lookup_allowed(lookup, lookup_value, request), True)