def test_classbased_technical_500(self):
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get("/classbased500/")
        self.assertContains(
            response,
            '<th scope="row">Raised during:</th>'
            "<td>view_tests.views.Raises500View</td>",
            status_code=500,
            html=True,
        )
        with self.assertLogs("django.request", "ERROR"):
            response = self.client.get(
                "/classbased500/", headers={"accept": "text/plain"}
            )
        self.assertContains(
            response,
            "Raised during: view_tests.views.Raises500View",
            status_code=500,
        )