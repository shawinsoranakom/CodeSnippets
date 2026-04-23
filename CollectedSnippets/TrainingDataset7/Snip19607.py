def test_filter_comments_by_pk_in(self):
        test_cases = (
            (),
            (self.comment_1,),
            (self.comment_1, self.comment_4),
        )

        for objs in test_cases:
            with self.subTest(objs=objs):
                pks = [obj.pk for obj in objs]
                self.assertSequenceEqual(
                    Comment.objects.filter(pk__in=pks).order_by("pk"), objs
                )