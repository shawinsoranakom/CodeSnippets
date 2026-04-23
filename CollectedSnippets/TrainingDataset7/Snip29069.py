def test_overriding_get_exclude(self):
        class BandAdmin(ModelAdmin):
            def get_exclude(self, request, obj=None):
                return ["name"]

        self.assertEqual(
            list(BandAdmin(Band, self.site).get_form(request).base_fields),
            ["bio", "sign_date"],
        )