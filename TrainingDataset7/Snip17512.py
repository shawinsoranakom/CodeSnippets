def test_anonymous_has_no_permissions(self):
        """
        #17903 -- Anonymous users shouldn't have permissions in
        ModelBackend.get_(all|user|group)_permissions().
        """
        backend = ModelBackend()

        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Group)
        user_perm = Permission.objects.create(
            name="test", content_type=content_type, codename="test_user"
        )
        group_perm = Permission.objects.create(
            name="test2", content_type=content_type, codename="test_group"
        )
        user.user_permissions.add(user_perm)

        group = Group.objects.create(name="test_group")
        user.groups.add(group)
        group.permissions.add(group_perm)

        self.assertEqual(
            backend.get_all_permissions(user), {"auth.test_user", "auth.test_group"}
        )
        self.assertEqual(backend.get_user_permissions(user), {"auth.test_user"})
        self.assertEqual(backend.get_group_permissions(user), {"auth.test_group"})

        with mock.patch.object(self.UserModel, "is_anonymous", True):
            self.assertEqual(backend.get_all_permissions(user), set())
            self.assertEqual(backend.get_user_permissions(user), set())
            self.assertEqual(backend.get_group_permissions(user), set())