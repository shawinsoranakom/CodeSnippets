def test_14377(self):
        # Bug 14377
        self.login()
        response = self.client.post("/logout/")
        self.assertIn("site", response.context)