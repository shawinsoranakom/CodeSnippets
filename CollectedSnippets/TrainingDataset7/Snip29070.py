def test_get_exclude_overrides_exclude(self):
        class BandAdmin(ModelAdmin):
            exclude = ["bio"]

            def get_exclude(self, request, obj=None):
                return ["name"]

        self.assertEqual(
            list(BandAdmin(Band, self.site).get_form(request).base_fields),
            ["bio", "sign_date"],
        )