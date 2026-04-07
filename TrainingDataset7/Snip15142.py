def test_builtin_lookup_in_search_fields(self):
        band = Group.objects.create(name="The Hype")
        concert = Concert.objects.create(name="Woodstock", group=band)

        m = ConcertAdmin(Concert, custom_site)
        m.search_fields = ["name__iexact"]

        request = self.factory.get("/", data={SEARCH_VAR: "woodstock"})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [concert])

        request = self.factory.get("/", data={SEARCH_VAR: "wood"})
        request.user = self.superuser
        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [])