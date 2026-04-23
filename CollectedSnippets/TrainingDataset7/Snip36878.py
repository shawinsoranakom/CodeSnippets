def test_technical_500_content_type_negotiation(self):
        for accepts, content_type in [
            ("text/plain", "text/plain; charset=utf-8"),
            ("text/html", "text/html"),
            ("text/html,text/plain;q=0.9", "text/html"),
            ("text/plain,text/html;q=0.9", "text/plain; charset=utf-8"),
            ("text/*", "text/html"),
        ]:
            with self.subTest(accepts=accepts):
                with self.assertLogs("django.request", "ERROR"):
                    response = self.client.get(
                        "/raises500/", headers={"accept": accepts}
                    )
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response["Content-Type"], content_type)