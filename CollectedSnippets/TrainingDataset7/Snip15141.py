def test_pk_in_search_fields(self):
        band = Group.objects.create(name="The Hype")
        Concert.objects.create(name="Woodstock", group=band)

        m = ConcertAdmin(Concert, custom_site)
        m.search_fields = ["group__pk"]

        request = self.factory.get("/concert/", data={SEARCH_VAR: band.pk})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertEqual(cl.queryset.count(), 1)

        request = self.factory.get("/concert/", data={SEARCH_VAR: band.pk + 5})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertEqual(cl.queryset.count(), 0)