def test_adminsite_display_site_url(self):
        """
        #13749 - Admin should display link to front-end site 'View site'
        """
        url = reverse("admin:index")
        response = self.client.get(url)
        self.assertEqual(response.context["site_url"], "/my-site-url/")
        self.assertContains(response, '<a href="/my-site-url/">View site</a>')