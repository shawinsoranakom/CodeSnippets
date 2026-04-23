def test_index_css_classes(self):
        """
        CSS class names are used for each app and model on the admin index
        pages (#17050).
        """
        # General index page
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, '<div class="app-admin_views module')
        self.assertContains(
            response,
            '<thead class="visually-hidden"><tr><th scope="col">Model name</th>'
            '<th scope="col">Add link</th><th scope="col">Change or view list link</th>'
            "</tr></thead>",
            html=True,
        )
        self.assertContains(response, '<tr class="model-actor">')
        self.assertContains(response, '<tr class="model-album">')

        # App index page
        response = self.client.get(reverse("admin:app_list", args=("admin_views",)))
        self.assertContains(response, '<div class="app-admin_views module')
        self.assertContains(
            response,
            '<thead class="visually-hidden"><tr><th scope="col">Model name</th>'
            '<th scope="col">Add link</th><th scope="col">Change or view list link</th>'
            "</tr></thead>",
            html=True,
        )
        self.assertContains(response, '<tr class="model-actor">')
        self.assertContains(response, '<tr class="model-album">')