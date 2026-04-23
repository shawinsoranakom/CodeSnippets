def test_get_user_permissions(self):
        self.assertEqual(self.user.get_user_permissions(), {"user_perm"})