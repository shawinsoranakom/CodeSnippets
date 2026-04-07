def test_groups_for_user(self):
        """
        groups_for_user() returns correct values as per
        https://modwsgi.readthedocs.io/en/develop/user-guides/access-control-mechanisms.html#apache-group-authorisation
        """
        user1 = User.objects.create_user("test", "test@example.com", "test")
        User.objects.create_user("test1", "test1@example.com", "test1")
        group = Group.objects.create(name="test_group")
        user1.groups.add(group)

        # User not in database
        self.assertEqual(groups_for_user({}, "unknown"), [])

        self.assertEqual(groups_for_user({}, "test"), [b"test_group"])
        self.assertEqual(groups_for_user({}, "test1"), [])