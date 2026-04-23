def test_filter_and_count_users_by_comments_fields(self):
        users = User.objects.filter(comments__id__gt=2).order_by("pk")
        self.assertEqual(users.count(), 4)
        self.assertSequenceEqual(
            users, (self.user_1, self.user_3, self.user_3, self.user_3)
        )

        users = User.objects.filter(comments__text__icontains="foo").order_by("pk")
        self.assertEqual(users.count(), 3)
        self.assertSequenceEqual(users, (self.user_1, self.user_2, self.user_3))

        users = User.objects.filter(comments__text__icontains="baz").order_by("pk")
        self.assertEqual(users.count(), 3)
        self.assertSequenceEqual(users, (self.user_3, self.user_3, self.user_3))