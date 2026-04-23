def test_filter_users_by_comments_gte(self):
        c11, c12, c13, c24, c15 = (
            self.comment_1,
            self.comment_2,
            self.comment_3,
            self.comment_4,
            self.comment_5,
        )
        u1, u2, u3 = (
            self.user_1,
            self.user_2,
            self.user_3,
        )
        test_cases = (
            (c11, (u1, u1, u1, u2, u3)),
            (c12, (u1, u1, u2, u3)),
            (c13, (u1, u2, u3)),
            (c15, (u1, u3)),
            (c24, (u3,)),
        )

        for comment, users in test_cases:
            with self.subTest(comment=comment, users=users):
                self.assertSequenceEqual(
                    User.objects.filter(comments__gte=comment).order_by("pk"), users
                )