def test_permissions(self):
        token = ContentType.objects.get_for_model(Token)
        user = ContentType.objects.get_for_model(User)
        comment = ContentType.objects.get_for_model(Comment)
        self.assertEqual(4, token.permission_set.count())
        self.assertEqual(4, user.permission_set.count())
        self.assertEqual(4, comment.permission_set.count())