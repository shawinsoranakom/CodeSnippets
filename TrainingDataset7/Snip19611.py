def test_filter_comments_by_user_and_order_by_pk_asc(self):
        self.assertSequenceEqual(
            Comment.objects.filter(user=self.user_1).order_by("pk"),
            (self.comment_1, self.comment_2, self.comment_5),
        )