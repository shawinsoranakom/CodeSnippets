def test_filter_users_by_comments_in(self):
        c1, c2, c3, c4, c5 = (
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
            ((), ()),
            ((c1,), (u1,)),
            ((c1, c2), (u1, u1)),
            ((c1, c2, c3), (u1, u1, u2)),
            ((c1, c2, c3, c4), (u1, u1, u2, u3)),
            ((c1, c2, c3, c4, c5), (u1, u1, u1, u2, u3)),
        )

        for comments, users in test_cases:
            with self.subTest(comments=comments, users=users):
                self.assertSequenceEqual(
                    User.objects.filter(comments__in=comments).order_by("pk"), users
                )