def test_specified_ordering(self):
        """
        Let's use a custom ModelAdmin that changes the ordering, and make sure
        it actually changes.
        """

        class BandAdmin(ModelAdmin):
            ordering = ("rank",)  # default ordering is ('name',)

        ma = BandAdmin(Band, site)
        names = [b.name for b in ma.get_queryset(request)]
        self.assertEqual(["Radiohead", "Van Halen", "Aerosmith"], names)