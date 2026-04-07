def test_group_natural_key(self):
        users_group = Group.objects.create(name="users")
        self.assertEqual(Group.objects.get_by_natural_key("users"), users_group)