def test_filter_comments_by_user_and_contains(self):
        self.assertIs(
            Comment.objects.filter(user=self.user_1).contains(self.comment_1), True
        )