def test_save(self):
        self.session.save()
        self.assertIs(self.session.exists(self.session.session_key), True)