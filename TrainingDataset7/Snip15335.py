def test_view_index(self):
        response = self.client.get(reverse("django-admindocs-views-index"))
        self.assertContains(
            response,
            '<h3><a href="/admindocs/views/django.contrib.admindocs.views.'
            'BaseAdminDocsView/">/admindocs/</a></h3>',
            html=True,
        )
        self.assertContains(response, "Views by namespace test")
        self.assertContains(response, "Name: <code>test:func</code>.")
        self.assertContains(
            response,
            '<h3><a href="/admindocs/views/admin_docs.views.XViewCallableObject/">'
            "/xview/callable_object_without_xview/</a></h3>",
            html=True,
        )