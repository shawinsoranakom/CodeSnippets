def test_test_cookie(self):
        self.assertIs(self.session.has_key(self.session.TEST_COOKIE_NAME), False)
        self.session.set_test_cookie()
        self.assertIs(self.session.test_cookie_worked(), True)
        self.session.delete_test_cookie()
        self.assertIs(self.session.has_key(self.session.TEST_COOKIE_NAME), False)