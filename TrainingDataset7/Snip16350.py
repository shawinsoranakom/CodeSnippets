def test_formset_kwargs_can_be_overridden(self):
        response = self.client.get(reverse("admin:admin_views_city_add"))
        self.assertContains(response, "overridden_name")