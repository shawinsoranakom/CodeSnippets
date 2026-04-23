def confirm_logged_out(self):
        self.assertNotIn(SESSION_KEY, self.client.session)