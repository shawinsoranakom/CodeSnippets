def test_redirect_fallback_flatpage_root(self):
        """
        A flatpage at / should not cause a redirect loop when APPEND_SLASH is
        set
        """
        fp = FlatPage.objects.create(
            url="/",
            title="Root",
            content="Root",
            enable_comments=False,
            registration_required=False,
        )
        fp.sites.add(settings.SITE_ID)

        response = self.client.get("/")
        self.assertContains(response, "<p>Root</p>")