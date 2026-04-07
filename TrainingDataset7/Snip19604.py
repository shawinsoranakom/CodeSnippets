def test_filter_comments_by_pk_gte(self):
        c11, c12, c13, c24, c15 = (
            self.comment_1,
            self.comment_2,
            self.comment_3,
            self.comment_4,
            self.comment_5,
        )
        test_cases = (
            (c11, (c11, c12, c13, c15, c24)),
            (c12, (c12, c13, c15, c24)),
            (c13, (c13, c15, c24)),
            (c15, (c15, c24)),
            (c24, (c24,)),
        )

        for obj, objs in test_cases:
            with self.subTest(obj=obj, objs=objs):
                self.assertSequenceEqual(
                    Comment.objects.filter(pk__gte=obj.pk).order_by("pk"), objs
                )