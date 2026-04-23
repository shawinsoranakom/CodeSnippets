def test_delete(self):
        self.session.save()
        self.session.delete(self.session.session_key)
        self.assertIs(self.session.exists(self.session.session_key), False)