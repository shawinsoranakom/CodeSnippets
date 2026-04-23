def test_delete_user_by_pk(self):
        result = User.objects.filter(pk=self.user_1.pk).delete()

        self.assertEqual(
            result, (2, {"composite_pk.User": 1, "composite_pk.Comment": 1})
        )

        self.assertIs(User.objects.filter(pk=self.user_1.pk).exists(), False)
        self.assertIs(User.objects.filter(pk=self.user_2.pk).exists(), True)
        self.assertIs(Comment.objects.filter(pk=self.comment_1.pk).exists(), False)
        self.assertIs(Comment.objects.filter(pk=self.comment_2.pk).exists(), True)
        self.assertIs(Comment.objects.filter(pk=self.comment_3.pk).exists(), True)