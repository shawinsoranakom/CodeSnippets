def test_session_key_is_read_only(self):
        def set_session_key(session):
            session.session_key = session._get_new_session_key()

        with self.assertRaises(AttributeError):
            set_session_key(self.session)