def test_filter_users_by_comments_isnull(self):
        u1, u2, u3, u4 = (
            self.user_1,
            self.user_2,
            self.user_3,
            self.user_4,
        )

        with self.subTest("comments__isnull=True"):
            self.assertSequenceEqual(
                User.objects.filter(comments__isnull=True).order_by("pk"),
                (u4,),
            )
        with self.subTest("comments__isnull=False"):
            self.assertSequenceEqual(
                User.objects.filter(comments__isnull=False).order_by("pk"),
                (u1, u1, u1, u2, u3),
            )