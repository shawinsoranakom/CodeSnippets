def test_get_exclude_takes_obj(self):
        class BandAdmin(ModelAdmin):
            def get_exclude(self, request, obj=None):
                if obj:
                    return ["sign_date"]
                return ["name"]

        self.assertEqual(
            list(BandAdmin(Band, self.site).get_form(request, self.band).base_fields),
            ["name", "bio"],
        )