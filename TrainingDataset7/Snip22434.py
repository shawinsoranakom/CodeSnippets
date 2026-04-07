def test_prefetch_foreignobject_reverse(self):
        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        Membership.objects.create(
            membership_country=self.usa, person=self.jim, group=self.democrat
        )
        with self.assertNumQueries(2):
            membership_sets = [
                list(p.membership_set.all())
                for p in Person.objects.prefetch_related("membership_set").order_by(
                    "pk"
                )
            ]

        with self.assertNumQueries(7):
            normal_membership_sets = [
                list(p.membership_set.all()) for p in Person.objects.order_by("pk")
            ]
        self.assertEqual(membership_sets, normal_membership_sets)