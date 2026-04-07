def test_template_override_exception_reporter(self):
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get("/raises500/")
        self.assertContains(
            response,
            "<h1>Oh no, an error occurred!</h1>",
            status_code=500,
            html=True,
        )

        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get("/raises500/", headers={"accept": "text/plain"})
        self.assertContains(response, "Oh dear, an error occurred!", status_code=500)