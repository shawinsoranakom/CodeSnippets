def test_400(self):
        # When DEBUG=True, technical_500_template() is called.
        with self.assertLogs("django.security", "WARNING"):
            response = self.client.get("/raises400/")
        self.assertContains(response, '<div class="context" id="', status_code=400)