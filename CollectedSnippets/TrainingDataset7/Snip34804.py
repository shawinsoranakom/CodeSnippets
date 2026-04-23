def test_logout_with_custom_auth_backend(self):
        "Request a logout after logging in with custom authentication backend"

        def listener(*args, **kwargs):
            self.assertEqual(kwargs["sender"], CustomUser)
            listener.executed = True

        listener.executed = False
        u = CustomUser.custom_objects.create(email="test@test.com")
        u.set_password("password")
        u.save()

        user_logged_out.connect(listener)
        self.client.login(username="test@test.com", password="password")
        self.client.logout()
        user_logged_out.disconnect(listener)
        self.assertTrue(listener.executed)