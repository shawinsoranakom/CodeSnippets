def test_redirect_view_flatpage_special_chars(self):
        """
        A flatpage with special chars in the URL can be served through a view
        and should add a slash.
        """
        fp = FlatPage.objects.create(
            url="/some.very_special~chars-here/",
            title="A very special page",
            content="Isn't it special!",
            enable_comments=False,
            registration_required=False,
        )
        fp.sites.add(settings.SITE_ID)

        response = self.client.get("/flatpage_root/some.very_special~chars-here")
        self.assertRedirects(
            response, "/flatpage_root/some.very_special~chars-here/", status_code=301
        )