def test_distinct_for_many_to_many_at_second_level_in_search_fields(self):
        """
        When using a ManyToMany in search_fields at the second level behind a
        ForeignKey, distinct() must be called and results shouldn't appear more
        than once.
        """
        lead = Musician.objects.create(name="Vox")
        band = Group.objects.create(name="The Hype")
        Concert.objects.create(name="Woodstock", group=band)
        Membership.objects.create(group=band, music=lead, role="lead voice")
        Membership.objects.create(group=band, music=lead, role="bass player")

        m = ConcertAdmin(Concert, custom_site)
        request = self.factory.get("/concert/", data={SEARCH_VAR: "vox"})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        # There's only one Concert instance
        self.assertEqual(cl.queryset.count(), 1)
        # Queryset must be deletable.
        cl.queryset.delete()
        self.assertEqual(cl.queryset.count(), 0)