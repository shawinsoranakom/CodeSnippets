def test_prefetch_foreignobject_null_hidden_forward_skipped(self):
        fiendship = Friendship.objects.create(
            from_friend_country=self.usa,
            from_friend_id=self.bob.id,
            to_friend_country_id=self.usa.id,
            to_friend_id=None,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                Friendship.objects.prefetch_related("to_friend").get(),
                fiendship,
            )