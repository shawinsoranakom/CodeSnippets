def test_confirm_valid(self):
        url, path = self._test_confirm_start()
        response = self.client.get(path)
        # redirect to a 'complete' page:
        self.assertContains(response, "Please enter your new password")