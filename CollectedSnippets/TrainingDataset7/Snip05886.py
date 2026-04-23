def tearDown(self):
        # Ensure that no CSP violations were logged in the browser.
        self.assertEqual(self.get_browser_logs(source="security"), [])
        super().tearDown()