def test_filter_comments_by_user_and_exclude_by_pk(self):
        self.assertSequenceEqual(
            Comment.objects.filter(user=self.user_1)
            .exclude(pk=self.comment_1.pk)
            .order_by("pk"),
            (self.comment_2, self.comment_5),
        )