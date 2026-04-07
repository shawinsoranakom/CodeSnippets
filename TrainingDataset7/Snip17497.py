def test_get_all_permissions(self):
        self.assertEqual(self.user.get_all_permissions(), {"user_perm", "group_perm"})