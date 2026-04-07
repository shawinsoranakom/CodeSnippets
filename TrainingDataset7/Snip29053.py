def test_modeladmin_str(self):
        ma = ModelAdmin(Band, self.site)
        self.assertEqual(str(ma), "modeladmin.ModelAdmin")