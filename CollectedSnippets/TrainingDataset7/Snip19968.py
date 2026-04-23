def test_debug(self):
        url = "/debug/"
        # We should have the debug flag in the template.
        response = self.client.get(url)
        self.assertContains(response, "Have debug")

        # And now we should not
        with override_settings(DEBUG=False):
            response = self.client.get(url)
            self.assertNotContains(response, "Have debug")