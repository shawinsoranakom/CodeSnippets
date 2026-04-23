def test_prefetch_related_m2m_forward_works(self):
        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        Membership.objects.create(
            membership_country=self.usa, person=self.jim, group=self.democrat
        )

        with self.assertNumQueries(2):
            members_lists = [
                list(g.members.all()) for g in Group.objects.prefetch_related("members")
            ]

        normal_members_lists = [list(g.members.all()) for g in Group.objects.all()]
        self.assertEqual(members_lists, normal_members_lists)