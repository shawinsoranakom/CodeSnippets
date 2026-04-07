def test_external_redirect_with_fetch_error_msg(self):
        """
        assertRedirects without fetch_redirect_response=False raises
        a relevant ValueError rather than a non-descript AssertionError.
        """
        response = self.client.get("/django_project_redirect/")
        msg = (
            "The test client is unable to fetch remote URLs (got "
            "https://www.djangoproject.com/). If the host is served by Django, "
            "add 'www.djangoproject.com' to ALLOWED_HOSTS. "
            "Otherwise, use assertRedirects(..., fetch_redirect_response=False)."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.assertRedirects(response, "https://www.djangoproject.com/")