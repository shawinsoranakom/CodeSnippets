def test_user_is_created_and_added_to_group(self):
        user = User.objects.get(username="my_username")
        group = Group.objects.get(name="my_group")
        self.assertEqual(group, user.groups.get())