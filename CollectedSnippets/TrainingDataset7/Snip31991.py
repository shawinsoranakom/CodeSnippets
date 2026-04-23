def test_bool(self):
        # Empty session is falsy
        self.assertIs(bool(self.session), False)
        # Session with data is truthy
        self.session["foo"] = "bar"
        self.assertIs(bool(self.session), True)
        # Session with key but no data is truthy
        session_with_key = SessionBase()
        session_with_key._session_key = "testkey1234"
        self.assertIs(bool(session_with_key), True)