def test_field_arguments_restricted_on_form(self):
        # If fields or fieldsets is specified, it should exclude fields on the
        # Form class to the fields specified. This may cause errors to be
        # raised in the db layer if required model fields aren't in fields/
        # fieldsets, but that's preferable to ghost errors where a field in the
        # Form class isn't being displayed because it's not in
        # fields/fieldsets.

        # Using `fields`.
        class BandAdmin(ModelAdmin):
            fields = ["name"]

        ma = BandAdmin(Band, self.site)
        self.assertEqual(list(ma.get_form(request).base_fields), ["name"])
        self.assertEqual(list(ma.get_form(request, self.band).base_fields), ["name"])

        # Using `fieldsets`.
        class BandAdmin(ModelAdmin):
            fieldsets = [(None, {"fields": ["name"]})]

        ma = BandAdmin(Band, self.site)
        self.assertEqual(list(ma.get_form(request).base_fields), ["name"])
        self.assertEqual(list(ma.get_form(request, self.band).base_fields), ["name"])

        # Using `exclude`.
        class BandAdmin(ModelAdmin):
            exclude = ["bio"]

        ma = BandAdmin(Band, self.site)
        self.assertEqual(list(ma.get_form(request).base_fields), ["name", "sign_date"])

        # You can also pass a tuple to `exclude`.
        class BandAdmin(ModelAdmin):
            exclude = ("bio",)

        ma = BandAdmin(Band, self.site)
        self.assertEqual(list(ma.get_form(request).base_fields), ["name", "sign_date"])

        # Using `fields` and `exclude`.
        class BandAdmin(ModelAdmin):
            fields = ["name", "bio"]
            exclude = ["bio"]

        ma = BandAdmin(Band, self.site)
        self.assertEqual(list(ma.get_form(request).base_fields), ["name"])