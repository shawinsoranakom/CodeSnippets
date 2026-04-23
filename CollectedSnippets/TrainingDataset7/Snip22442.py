def test_prefetch_related_m2m_reverse_works(self):
        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        Membership.objects.create(
            membership_country=self.usa, person=self.jim, group=self.democrat
        )

        with self.assertNumQueries(2):
            groups_lists = [
                list(p.groups.all()) for p in Person.objects.prefetch_related("groups")
            ]

        normal_groups_lists = [list(p.groups.all()) for p in Person.objects.all()]
        self.assertEqual(groups_lists, normal_groups_lists)