def test_default_urlconf_technical_404(self):
        response = self.client.get("/favicon.ico")
        self.assertContains(
            response,
            "<code>\nadmin/\n[namespace='admin']\n</code>",
            status_code=404,
            html=True,
        )