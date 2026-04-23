def test_modeladmin_repr(self):
        ma = ModelAdmin(Band, self.site)
        self.assertEqual(
            repr(ma),
            "<ModelAdmin: model=Band site=AdminSite(name='admin')>",
        )