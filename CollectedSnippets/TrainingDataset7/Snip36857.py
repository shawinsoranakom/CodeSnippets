def test_translation(self):
        """An invalid request is rejected with a localized error message."""
        response = self.client.post("/")
        self.assertContains(response, "Forbidden", status_code=403)
        self.assertContains(
            response, "CSRF verification failed. Request aborted.", status_code=403
        )

        with self.settings(LANGUAGE_CODE="nl"), override("en-us"):
            response = self.client.post("/")
            self.assertContains(response, "Verboden", status_code=403)
            self.assertContains(
                response,
                "CSRF-verificatie mislukt. Verzoek afgebroken.",
                status_code=403,
            )