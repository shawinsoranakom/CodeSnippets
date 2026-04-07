def setUp(self):
        """Set up the listeners and reset the logged in/logged out counters"""
        self.logged_in = []
        self.logged_out = []
        self.login_failed = []
        signals.user_logged_in.connect(self.listener_login)
        self.addCleanup(signals.user_logged_in.disconnect, self.listener_login)
        signals.user_logged_out.connect(self.listener_logout)
        self.addCleanup(signals.user_logged_out.disconnect, self.listener_logout)
        signals.user_login_failed.connect(self.listener_login_failed)
        self.addCleanup(
            signals.user_login_failed.disconnect, self.listener_login_failed
        )