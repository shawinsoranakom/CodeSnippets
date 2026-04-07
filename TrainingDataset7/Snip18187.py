def test_passing_explicit_none(self):
        msg = "get_response must be provided."
        with self.assertRaisesMessage(ValueError, msg):
            RemoteUserMiddleware(None)