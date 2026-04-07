def test_default_fields(self):
        ma = ModelAdmin(Band, self.site)
        self.assertEqual(
            list(ma.get_form(request).base_fields), ["name", "bio", "sign_date"]
        )
        self.assertEqual(list(ma.get_fields(request)), ["name", "bio", "sign_date"])
        self.assertEqual(
            list(ma.get_fields(request, self.band)), ["name", "bio", "sign_date"]
        )
        self.assertIsNone(ma.get_exclude(request, self.band))