def test_new_session(self):
        self.assertIs(self.session.modified, False)
        self.assertIs(self.session.accessed, False)