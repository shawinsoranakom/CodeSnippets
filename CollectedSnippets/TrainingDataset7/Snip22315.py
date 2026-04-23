def test_fallback_flatpage_special_chars(self):
        """
        A flatpage with special chars in the URL can be served by the fallback
        middleware.
        """
        fp = FlatPage.objects.create(
            url="/some.very_special~chars-here/",
            title="A very special page",
            content="Isn't it special!",
            enable_comments=False,
            registration_required=False,
        )
        fp.sites.add(settings.SITE_ID)

        response = self.client.get("/some.very_special~chars-here/")
        self.assertContains(response, "<p>Isn't it special!</p>")