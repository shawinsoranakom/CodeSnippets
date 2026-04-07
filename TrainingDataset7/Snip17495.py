def test_get_group_permissions(self):
        self.assertEqual(self.user.get_group_permissions(), {"group_perm"})