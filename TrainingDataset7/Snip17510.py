def test_has_no_object_perm(self):
        """Regressiontest for #12462"""
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        content_type = ContentType.objects.get_for_model(Group)
        perm = Permission.objects.create(
            name="test", content_type=content_type, codename="test"
        )
        user.user_permissions.add(perm)

        self.assertIs(user.has_perm("auth.test", "object"), False)
        self.assertEqual(user.get_all_permissions("object"), set())
        self.assertIs(user.has_perm("auth.test"), True)
        self.assertEqual(user.get_all_permissions(), {"auth.test"})