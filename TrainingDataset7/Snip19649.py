def test_get_user_by_comments(self):
        self.assertEqual(User.objects.get(comments=self.comment_1), self.user_1)