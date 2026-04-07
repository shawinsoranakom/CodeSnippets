def test_technical_500(self):
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get("/raises500/")
        self.assertContains(response, '<header id="summary">', status_code=500)
        self.assertContains(response, '<main id="info">', status_code=500)
        self.assertContains(response, '<footer id="explanation">', status_code=500)
        self.assertContains(
            response,
            '<th scope="row">Raised during:</th><td>view_tests.views.raises500</td>',
            status_code=500,
            html=True,
        )
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get("/raises500/", headers={"accept": "text/plain"})
        self.assertContains(
            response,
            "Raised during: view_tests.views.raises500",
            status_code=500,
        )