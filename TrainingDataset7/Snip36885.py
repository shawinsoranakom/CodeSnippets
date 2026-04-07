def test_default_urlconf_template(self):
        """
        Make sure that the default URLconf template is shown instead of the
        technical 404 page, if the user has not altered their URLconf yet.
        """
        response = self.client.get("/")
        self.assertContains(
            response, "<h1>The install worked successfully! Congratulations!</h1>"
        )