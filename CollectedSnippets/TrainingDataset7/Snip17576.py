def test_has_perm(self):
        content_type = ContentType.objects.get_for_model(Group)
        perm = Permission.objects.create(
            name="test", content_type=content_type, codename="test"
        )
        self.user1.user_permissions.add(perm)

        self.assertIs(self.user1.has_perm("auth.test"), True)
        self.assertIs(self.user1.has_module_perms("auth"), True)