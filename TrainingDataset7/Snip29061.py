def test_lookup_allowed_non_autofield_primary_key(self):
        class Country(models.Model):
            id = models.CharField(max_length=2, primary_key=True)

        class Place(models.Model):
            country = models.ForeignKey(Country, models.CASCADE)

        class PlaceAdmin(ModelAdmin):
            list_filter = ["country"]

        ma = PlaceAdmin(Place, self.site)
        self.assertIs(ma.lookup_allowed("country__id__exact", "DE", request), True)