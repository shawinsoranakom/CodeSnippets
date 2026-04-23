def test_default_attributes(self):
        ma = ModelAdmin(Band, self.site)
        self.assertEqual(ma.actions, ())
        self.assertEqual(ma.inlines, ())