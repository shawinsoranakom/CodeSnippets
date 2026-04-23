def test_field_arguments(self):
        # If fields is specified, fieldsets_add and fieldsets_change should
        # just stick the fields into a formsets structure and return it.
        class BandAdmin(ModelAdmin):
            fields = ["name"]

        ma = BandAdmin(Band, self.site)

        self.assertEqual(list(ma.get_fields(request)), ["name"])
        self.assertEqual(list(ma.get_fields(request, self.band)), ["name"])
        self.assertEqual(ma.get_fieldsets(request), [(None, {"fields": ["name"]})])
        self.assertEqual(
            ma.get_fieldsets(request, self.band), [(None, {"fields": ["name"]})]
        )