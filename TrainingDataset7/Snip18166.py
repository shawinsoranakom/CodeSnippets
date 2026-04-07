def test_builtin_user_isactive(self):
        user = User.objects.create(username="foo", email="foo@bar.com")
        # is_active is true by default
        self.assertIs(user.is_active, True)
        user.is_active = False
        user.save()
        user_fetched = User.objects.get(pk=user.pk)
        # the is_active flag is saved
        self.assertFalse(user_fetched.is_active)