def test_permission_denied(self):
        """
        user is not authenticated after a backend raises permission denied
        #2550
        """
        self.assertIsNone(authenticate(username="test", password="test"))
        # user_login_failed signal is sent.
        self.assertEqual(
            self.user_login_failed,
            [{"password": "********************", "username": "test"}],
        )