def test_prefetch_foreignobject_hidden_forward(self):
        Friendship.objects.create(
            from_friend_country=self.usa,
            from_friend_id=self.bob.id,
            to_friend_country_id=self.usa.id,
            to_friend_id=self.george.id,
        )
        Friendship.objects.create(
            from_friend_country=self.usa,
            from_friend_id=self.bob.id,
            to_friend_country_id=self.soviet_union.id,
            to_friend_id=self.sam.id,
        )
        with self.assertNumQueries(2) as ctx:
            friendships = list(
                Friendship.objects.prefetch_related("to_friend").order_by("pk")
            )
        prefetch_sql = ctx[-1]["sql"]
        # Prefetch queryset should be filtered by all foreign related fields
        # to prevent extra rows from being eagerly fetched.
        prefetch_where_sql = prefetch_sql.split("WHERE")[-1]
        for to_field_name in Friendship.to_friend.field.to_fields:
            to_field = Person._meta.get_field(to_field_name)
            with self.subTest(to_field=to_field):
                self.assertIn(
                    connection.ops.quote_name(to_field.column),
                    prefetch_where_sql,
                )
        self.assertNotIn(" JOIN ", prefetch_sql)
        with self.assertNumQueries(0):
            self.assertEqual(friendships[0].to_friend, self.george)
            self.assertEqual(friendships[1].to_friend, self.sam)