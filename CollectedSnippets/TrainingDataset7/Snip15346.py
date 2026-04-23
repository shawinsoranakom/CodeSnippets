def test_no_sites_framework(self):
        """
        Without the sites framework, should not access SITE_ID or Site
        objects. Deleting settings is fine here as UserSettingsHolder is used.
        """
        Site.objects.all().delete()
        del settings.SITE_ID
        response = self.client.get(reverse("django-admindocs-views-index"))
        self.assertContains(response, "View documentation")