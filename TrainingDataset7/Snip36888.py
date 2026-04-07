def test_regression_21530(self):
        """
        Regression test for bug #21530.

        If the admin app include is replaced with exactly one url
        pattern, then the technical 404 template should be displayed.

        The bug here was that an AttributeError caused a 500 response.
        """
        response = self.client.get("/")
        self.assertContains(
            response, "Page not found <small>(404)</small>", status_code=404
        )