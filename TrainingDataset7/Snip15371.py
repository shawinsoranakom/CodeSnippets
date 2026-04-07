def test_model_index_superuser(self):
        self.client.force_login(self.superuser)
        index_url = reverse("django-admindocs-models-index")
        response = self.client.get(index_url)
        self.assertContains(
            response,
            '<a href="/admindocs/models/admin_docs.family/">Family</a>',
            html=True,
        )
        self.assertContains(
            response,
            '<a href="/admindocs/models/admin_docs.person/">Person</a>',
            html=True,
        )
        self.assertContains(
            response,
            '<a href="/admindocs/models/admin_docs.company/">Company</a>',
            html=True,
        )