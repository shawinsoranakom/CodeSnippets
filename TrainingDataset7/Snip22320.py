def test_redirect_fallback_flatpage_special_chars(self):
        """
        A flatpage with special chars in the URL can be served by the fallback
        middleware and should add a slash.
        """
        fp = FlatPage.objects.create(
            url="/some.very_special~chars-here/",
            title="A very special page",
            content="Isn't it special!",
            enable_comments=False,
            registration_required=False,
        )
        fp.sites.add(settings.SITE_ID)

        response = self.client.get("/some.very_special~chars-here")
        self.assertRedirects(
            response, "/some.very_special~chars-here/", status_code=301
        )