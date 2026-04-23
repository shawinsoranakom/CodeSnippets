def test_current_site_in_context_after_login(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        if apps.is_installed("django.contrib.sites"):
            Site = apps.get_model("sites.Site")
            site = Site.objects.get_current()
            self.assertEqual(response.context["site"], site)
            self.assertEqual(response.context["site_name"], site.name)
        else:
            self.assertIsInstance(response.context["site"], RequestSite)
        self.assertIsInstance(response.context["form"], AuthenticationForm)