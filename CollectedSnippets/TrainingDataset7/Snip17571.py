async def test_aauthenticate_permission_denied(self):
        self.assertIsNone(await aauthenticate(username="test", password="test"))
        # user_login_failed signal is sent.
        self.assertEqual(
            self.user_login_failed,
            [{"password": "********************", "username": "test"}],
        )