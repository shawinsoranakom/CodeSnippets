def test_select_related_foreignkey_forward_works(self):
        Membership.objects.create(
            membership_country=self.usa, person=self.bob, group=self.cia
        )
        Membership.objects.create(
            membership_country=self.usa, person=self.jim, group=self.democrat
        )

        with self.assertNumQueries(1):
            people = [
                m.person
                for m in Membership.objects.select_related("person").order_by("pk")
            ]

        normal_people = [m.person for m in Membership.objects.order_by("pk")]
        self.assertEqual(people, normal_people)