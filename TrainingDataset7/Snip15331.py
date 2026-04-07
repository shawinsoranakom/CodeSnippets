def test_index(self):
        response = self.client.get(reverse("django-admindocs-docroot"))
        self.assertContains(response, "<h1>Documentation</h1>", html=True)
        self.assertContains(
            response,
            '<div id="site-name"><a href="/admin/">Django administration</a></div>',
        )
        self.client.logout()
        response = self.client.get(reverse("django-admindocs-docroot"), follow=True)
        # Should display the login screen
        self.assertContains(
            response, '<input type="hidden" name="next" value="/admindocs/">', html=True
        )