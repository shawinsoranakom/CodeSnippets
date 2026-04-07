def test_without_user(self):
        with self.assertRaisesMessage(
            AttributeError,
            "'NoneType' object has no attribute 'get_session_auth_hash'",
        ):
            auth.login(self.request, None)