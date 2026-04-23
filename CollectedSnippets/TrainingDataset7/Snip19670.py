def test_update_user(self):
        email = "user9315@example.com"
        result = User.objects.filter(pk=self.user_1.pk).update(email=email)
        self.assertEqual(result, 1)
        user = User.objects.get(pk=self.user_1.pk)
        self.assertEqual(user.email, email)