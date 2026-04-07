def test_m2m_through_on_self_works(self):
        self.assertQuerySetEqual(self.jane.friends.all(), [])

        Friendship.objects.create(
            from_friend_country=self.jane.person_country,
            from_friend=self.jane,
            to_friend_country=self.george.person_country,
            to_friend=self.george,
        )

        self.assertQuerySetEqual(
            self.jane.friends.all(), ["George"], attrgetter("name")
        )