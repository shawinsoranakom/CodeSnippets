def test_filter_comments_by_pk_isnull(self):
        c11, c12, c13, c24, c15 = (
            self.comment_1,
            self.comment_2,
            self.comment_3,
            self.comment_4,
            self.comment_5,
        )

        with self.subTest("pk__isnull=True"):
            self.assertSequenceEqual(
                Comment.objects.filter(pk__isnull=True).order_by("pk"),
                (),
            )
        with self.subTest("pk__isnull=False"):
            self.assertSequenceEqual(
                Comment.objects.filter(pk__isnull=False).order_by("pk"),
                (c11, c12, c13, c15, c24),
            )