def test_get_group_permissions(self):
        group = Group.objects.create(name="test_group")
        self.user3.groups.add(group)
        self.assertEqual(self.user3.get_group_permissions(TestObj()), {"group_perm"})