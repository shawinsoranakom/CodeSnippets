def test_update_comment_by_user_email(self):
        result = Comment.objects.filter(user__email=self.user_1.email).update(
            text="foo"
        )

        self.assertEqual(result, 2)
        comment_1 = Comment.objects.get(pk=self.comment_1.pk)
        comment_2 = Comment.objects.get(pk=self.comment_2.pk)
        self.assertEqual(comment_1.text, "foo")
        self.assertEqual(comment_2.text, "foo")