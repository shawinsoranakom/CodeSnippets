def test_distinct_for_inherited_m2m_in_list_filter(self):
        """
        Regression test for #13902: When using a ManyToMany in list_filter,
        results shouldn't appear more than once. Model managed in the
        admin inherits from the one that defines the relationship.
        """
        lead = Musician.objects.create(name="John")
        four = Quartet.objects.create(name="The Beatles")
        Membership.objects.create(group=four, music=lead, role="lead voice")
        Membership.objects.create(group=four, music=lead, role="guitar player")

        m = QuartetAdmin(Quartet, custom_site)
        request = self.factory.get("/quartet/", data={"members": lead.pk})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        cl.get_results(request)

        # There's only one Quartet instance
        self.assertEqual(cl.result_count, 1)
        # Queryset must be deletable.
        cl.queryset.delete()
        self.assertEqual(cl.queryset.count(), 0)