def test_shortcut_view_with_site_m2m(self, get_model):
        """
        When the object has a ManyToManyField to Site, redirect to the current
        site if it's attached to the object or to the domain of the first site
        found in the m2m relationship.
        """
        get_model.side_effect = lambda *args, **kwargs: (
            MockSite if args[0] == "sites.Site" else ModelWithM2MToSite
        )

        # get_current_site() will lookup a Site object, so these must match the
        # domains in the MockSite model.
        MockSite.objects.bulk_create(
            [
                MockSite(pk=1, domain="example.com"),
                MockSite(pk=self.site_2.pk, domain=self.site_2.domain),
                MockSite(pk=self.site_3.pk, domain=self.site_3.domain),
            ]
        )
        ct = ContentType.objects.get_for_model(ModelWithM2MToSite)
        site_3_obj = ModelWithM2MToSite.objects.create(
            title="Not Linked to Current Site"
        )
        site_3_obj.sites.add(MockSite.objects.get(pk=self.site_3.pk))
        expected_url = "http://%s%s" % (
            self.site_3.domain,
            site_3_obj.get_absolute_url(),
        )

        with self.settings(SITE_ID=self.site_2.pk):
            # Redirects to the domain of the first Site found in the m2m
            # relationship (ordering is arbitrary).
            response = self.client.get("/shortcut/%s/%s/" % (ct.pk, site_3_obj.pk))
            self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        obj_with_sites = ModelWithM2MToSite.objects.create(
            title="Linked to Current Site"
        )
        obj_with_sites.sites.set(MockSite.objects.all())
        shortcut_url = "/shortcut/%s/%s/" % (ct.pk, obj_with_sites.pk)
        expected_url = "http://%s%s" % (
            self.site_2.domain,
            obj_with_sites.get_absolute_url(),
        )

        with self.settings(SITE_ID=self.site_2.pk):
            # Redirects to the domain of the Site matching the current site's
            # domain.
            response = self.client.get(shortcut_url)
            self.assertRedirects(response, expected_url, fetch_redirect_response=False)

        with self.settings(SITE_ID=None, ALLOWED_HOSTS=[self.site_2.domain]):
            # Redirects to the domain of the Site matching the request's host
            # header.
            response = self.client.get(shortcut_url, SERVER_NAME=self.site_2.domain)
            self.assertRedirects(response, expected_url, fetch_redirect_response=False)