def test_filter_comments_by_pk_in_subquery(self):
        self.assertSequenceEqual(
            Comment.objects.filter(
                pk__in=Comment.objects.filter(pk=self.comment_1.pk),
            ),
            [self.comment_1],
        )
        self.assertSequenceEqual(
            Comment.objects.filter(
                pk__in=Comment.objects.filter(pk=self.comment_1.pk).values(
                    "tenant_id", "id"
                ),
            ),
            [self.comment_1],
        )
        self.comment_2.integer = self.comment_1.id
        self.comment_2.save()
        self.assertSequenceEqual(
            Comment.objects.filter(
                pk__in=Comment.objects.values("tenant_id", "integer"),
            ),
            [self.comment_1],
        )