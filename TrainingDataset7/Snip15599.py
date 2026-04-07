def test_dynamic_ordering(self):
        """
        Let's use a custom ModelAdmin that changes the ordering dynamically.
        """
        super_user = User.objects.create(username="admin", is_superuser=True)
        other_user = User.objects.create(username="other")
        request = self.request_factory.get("/")
        request.user = super_user
        ma = DynOrderingBandAdmin(Band, site)
        names = [b.name for b in ma.get_queryset(request)]
        self.assertEqual(["Radiohead", "Van Halen", "Aerosmith"], names)
        request.user = other_user
        names = [b.name for b in ma.get_queryset(request)]
        self.assertEqual(["Aerosmith", "Radiohead", "Van Halen"], names)