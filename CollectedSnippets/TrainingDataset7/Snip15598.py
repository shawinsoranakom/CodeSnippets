def test_specified_ordering_by_f_expression(self):
        class BandAdmin(ModelAdmin):
            ordering = (F("rank").desc(nulls_last=True),)

        band_admin = BandAdmin(Band, site)
        names = [b.name for b in band_admin.get_queryset(request)]
        self.assertEqual(["Aerosmith", "Van Halen", "Radiohead"], names)