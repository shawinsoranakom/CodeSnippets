def test_sidebar_model_name_non_ascii(self):
        url = reverse("test_with_sidebar:admin_views_héllo_changelist")
        response = self.client.get(url)
        self.assertContains(
            response, '<div class="app-admin_views module current-app">'
        )
        self.assertContains(response, '<tr class="model-héllo current-model">')
        self.assertContains(
            response,
            '<th scope="row" id="admin_views-héllo">'
            '<a href="/test_sidebar/admin/admin_views/h%C3%A9llo/" aria-current="page">'
            "Héllos</a></th>",
            html=True,
        )