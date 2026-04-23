def test_false(self):
        "The 'View on site' button is not displayed if view_on_site is False"
        response = self.client.get(
            reverse("admin:admin_views_restaurant_change", args=(self.r1.pk,))
        )
        content_type_pk = ContentType.objects.get_for_model(Restaurant).pk
        self.assertNotContains(
            response, reverse("admin:view_on_site", args=(content_type_pk, 1))
        )