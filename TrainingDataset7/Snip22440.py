def test_m2m_through_on_self_ignores_mismatch_columns(self):
        self.assertQuerySetEqual(self.jane.friends.all(), [])

        # Note that we use ids instead of instances. This is because instances
        # on ForeignObject properties will set all related field off of the
        # given instance.
        Friendship.objects.create(
            from_friend_id=self.jane.id,
            to_friend_id=self.george.id,
            to_friend_country_id=self.jane.person_country_id,
            from_friend_country_id=self.george.person_country_id,
        )

        self.assertQuerySetEqual(self.jane.friends.all(), [])