def test_custom_lookup_in_search_fields(self):
        band = Group.objects.create(name="The Hype")
        concert = Concert.objects.create(name="Woodstock", group=band)

        m = ConcertAdmin(Concert, custom_site)
        m.search_fields = ["group__name__cc"]
        with register_lookup(Field, Contains, lookup_name="cc"):
            request = self.factory.get("/", data={SEARCH_VAR: "Hype"})
            request.user = self.superuser
            cl = m.get_changelist_instance(request)
            self.assertCountEqual(cl.queryset, [concert])

            request = self.factory.get("/", data={SEARCH_VAR: "Woodstock"})
            request.user = self.superuser
            cl = m.get_changelist_instance(request)
            self.assertCountEqual(cl.queryset, [])