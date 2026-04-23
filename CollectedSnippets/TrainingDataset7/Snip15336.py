def test_view_index_with_method(self):
        """
        Views that are methods are listed correctly.
        """
        response = self.client.get(reverse("django-admindocs-views-index"))
        self.assertContains(
            response,
            "<h3>"
            '<a href="/admindocs/views/django.contrib.admin.sites.AdminSite.index/">'
            "/admin/</a></h3>",
            html=True,
        )