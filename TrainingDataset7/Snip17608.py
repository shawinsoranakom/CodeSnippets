def test_authenticate(self):
        self.assertFalse(self.user.is_active)
        self.assertEqual(authenticate(**self.user_credentials), self.user)