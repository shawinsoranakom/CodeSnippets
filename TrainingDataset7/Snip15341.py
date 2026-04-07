def test_view_detail_as_method(self):
        """
        Views that are methods can be displayed.
        """
        url = reverse(
            "django-admindocs-views-detail",
            args=["django.contrib.admin.sites.AdminSite.index"],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)