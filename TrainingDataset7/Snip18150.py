def test_user_double_save(self):
        """
        Calling user.save() twice should trigger password_changed() once.
        """
        user = User.objects.create_user(username="user", password="foo")
        user.set_password("bar")
        with mock.patch(
            "django.contrib.auth.password_validation.password_changed"
        ) as pw_changed:
            user.save()
            self.assertEqual(pw_changed.call_count, 1)
            user.save()
            self.assertEqual(pw_changed.call_count, 1)