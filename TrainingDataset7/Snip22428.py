def test_double_nested_query(self):
        m1 = Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.bob.id,
            group_id=self.cia.id,
        )
        m2 = Membership.objects.create(
            membership_country_id=self.usa.id,
            person_id=self.jim.id,
            group_id=self.cia.id,
        )
        Friendship.objects.create(
            from_friend_country_id=self.usa.id,
            from_friend_id=self.bob.id,
            to_friend_country_id=self.usa.id,
            to_friend_id=self.jim.id,
        )
        self.assertSequenceEqual(
            Membership.objects.filter(
                person__in=Person.objects.filter(
                    from_friend__in=Friendship.objects.filter(
                        to_friend__in=Person.objects.all()
                    )
                )
            ),
            [m1],
        )
        self.assertSequenceEqual(
            Membership.objects.exclude(
                person__in=Person.objects.filter(
                    from_friend__in=Friendship.objects.filter(
                        to_friend__in=Person.objects.all()
                    )
                )
            ),
            [m2],
        )