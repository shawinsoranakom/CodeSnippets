def test_login_failed(self):
        signal_calls = []

        def signal_handler(**kwargs):
            signal_calls.append(kwargs)

        user_login_failed.connect(signal_handler)
        fake_request = object()
        try:
            form = AuthenticationForm(
                fake_request,
                {
                    "username": "testclient",
                    "password": "incorrect",
                },
            )
            self.assertFalse(form.is_valid())
            self.assertIs(signal_calls[0]["request"], fake_request)
        finally:
            user_login_failed.disconnect(signal_handler)