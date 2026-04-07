def test_no_django_template_engine(self):
        """
        The CSRF view doesn't depend on the TEMPLATES configuration (#24388).
        """
        response = self.client.post("/")
        self.assertContains(response, "Forbidden", status_code=403)