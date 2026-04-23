def setUp(self):
        self.user_login_failed = []
        signals.user_login_failed.connect(self.user_login_failed_listener)
        self.addCleanup(
            signals.user_login_failed.disconnect, self.user_login_failed_listener
        )