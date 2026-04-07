def test_namespaced_view_detail(self):
        url = reverse(
            "django-admindocs-views-detail", args=["admin_docs.views.XViewClass"]
        )
        response = self.client.get(url)
        self.assertContains(response, "<h1>admin_docs.views.XViewClass</h1>")