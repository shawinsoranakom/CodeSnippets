def test_distinct_for_through_m2m_in_list_filter(self):
        """
        Regression test for #13902: When using a ManyToMany in list_filter,
        results shouldn't appear more than once. With an intermediate model.
        """
        lead = Musician.objects.create(name="Vox")
        band = Group.objects.create(name="The Hype")
        Membership.objects.create(group=band, music=lead, role="lead voice")
        Membership.objects.create(group=band, music=lead, role="bass player")

        m = GroupAdmin(Group, custom_site)
        request = self.factory.get("/group/", data={"members": lead.pk})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        cl.get_results(request)

        # There's only one Group instance
        self.assertEqual(cl.result_count, 1)
        # Queryset must be deletable.
        cl.queryset.delete()
        self.assertEqual(cl.queryset.count(), 0)