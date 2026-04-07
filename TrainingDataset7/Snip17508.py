def test_custom_perms(self):
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Group)
        perm = Permission.objects.create(
            name="test", content_type=content_type, codename="test"
        )
        user.user_permissions.add(perm)

        # reloading user to purge the _perm_cache
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        self.assertEqual(user.get_all_permissions(), {"auth.test"})
        self.assertEqual(user.get_user_permissions(), {"auth.test"})
        self.assertEqual(user.get_group_permissions(), set())
        self.assertIs(user.has_module_perms("Group"), False)
        self.assertIs(user.has_module_perms("auth"), True)

        perm = Permission.objects.create(
            name="test2", content_type=content_type, codename="test2"
        )
        user.user_permissions.add(perm)
        perm = Permission.objects.create(
            name="test3", content_type=content_type, codename="test3"
        )
        user.user_permissions.add(perm)
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        expected_user_perms = {"auth.test2", "auth.test", "auth.test3"}
        self.assertEqual(user.get_all_permissions(), expected_user_perms)
        self.assertIs(user.has_perm("test"), False)
        self.assertIs(user.has_perm("auth.test"), True)
        self.assertIs(user.has_perms(["auth.test2", "auth.test3"]), True)

        perm = Permission.objects.create(
            name="test_group", content_type=content_type, codename="test_group"
        )
        group = Group.objects.create(name="test_group")
        group.permissions.add(perm)
        user.groups.add(group)
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        self.assertEqual(
            user.get_all_permissions(), {*expected_user_perms, "auth.test_group"}
        )
        self.assertEqual(user.get_user_permissions(), expected_user_perms)
        self.assertEqual(user.get_group_permissions(), {"auth.test_group"})
        self.assertIs(user.has_perms(["auth.test3", "auth.test_group"]), True)

        user = AnonymousUser()
        self.assertIs(user.has_perm("test"), False)
        self.assertIs(user.has_perms(["auth.test2", "auth.test3"]), False)