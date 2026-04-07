def test_delete_comments_by_user(self):
        result = Comment.objects.filter(user=self.user_2).delete()

        self.assertEqual(result, (2, {"composite_pk.Comment": 2}))

        self.assertIs(Comment.objects.filter(pk=self.comment_1.pk).exists(), True)
        self.assertIs(Comment.objects.filter(pk=self.comment_2.pk).exists(), False)
        self.assertIs(Comment.objects.filter(pk=self.comment_3.pk).exists(), False)