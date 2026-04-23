def test_has_perm(self):
        user = self.UserModel._default_manager.get(pk=self.user.pk)
        self.assertIs(user.has_perm("auth.test"), False)

        user.is_staff = True
        user.save()
        self.assertIs(user.has_perm("auth.test"), False)

        user.is_superuser = True
        user.save()
        self.assertIs(user.has_perm("auth.test"), True)

        user.is_staff = True
        user.is_superuser = True
        user.is_active = False
        user.save()
        self.assertIs(user.has_perm("auth.test"), False)