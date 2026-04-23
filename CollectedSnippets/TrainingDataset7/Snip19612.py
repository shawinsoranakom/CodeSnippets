def test_filter_comments_by_user_and_order_by_pk_desc(self):
        self.assertSequenceEqual(
            Comment.objects.filter(user=self.user_1).order_by("-pk"),
            (self.comment_5, self.comment_2, self.comment_1),
        )