def test_spanning_relations_with_custom_lookup_in_search_fields(self):
        hype = Group.objects.create(name="The Hype")
        concert = Concert.objects.create(name="Woodstock", group=hype)
        vox = Musician.objects.create(name="Vox", age=20)
        Membership.objects.create(music=vox, group=hype)
        # Register a custom lookup on IntegerField to ensure that field
        # traversing logic in ModelAdmin.get_search_results() works.
        with register_lookup(IntegerField, Exact, lookup_name="exactly"):
            m = ConcertAdmin(Concert, custom_site)
            m.search_fields = ["group__members__age__exactly"]

            request = self.factory.get("/", data={SEARCH_VAR: "20"})
            request.user = self.superuser
            cl = m.get_changelist_instance(request)
            self.assertCountEqual(cl.queryset, [concert])

            request = self.factory.get("/", data={SEARCH_VAR: "21"})
            request.user = self.superuser
            cl = m.get_changelist_instance(request)
            self.assertCountEqual(cl.queryset, [])