def test_template_detail_loader(self):
        response = self.client.get(
            reverse("django-admindocs-templates", args=["view_for_loader_test.html"])
        )
        self.assertContains(response, "view_for_loader_test.html</code></li>")