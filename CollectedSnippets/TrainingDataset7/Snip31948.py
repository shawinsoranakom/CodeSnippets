def test_load_overlong_key(self):
        self.session._session_key = (string.ascii_letters + string.digits) * 20
        self.assertEqual(self.session.load(), {})