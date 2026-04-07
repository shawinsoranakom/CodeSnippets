def test_prefetch_foreignobject_forward(self):
        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        Membership.objects.create(
            membership_country=self.usa, person=self.jim, group=self.democrat
        )

        with self.assertNumQueries(2):
            people = [
                m.person
                for m in Membership.objects.prefetch_related("person").order_by("pk")
            ]

        normal_people = [m.person for m in Membership.objects.order_by("pk")]
        self.assertEqual(people, normal_people)