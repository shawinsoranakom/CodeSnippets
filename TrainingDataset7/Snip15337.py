def test_view_detail(self):
        url = reverse(
            "django-admindocs-views-detail",
            args=["django.contrib.admindocs.views.BaseAdminDocsView"],
        )
        response = self.client.get(url)
        # View docstring
        self.assertContains(response, "Base view for admindocs views.")