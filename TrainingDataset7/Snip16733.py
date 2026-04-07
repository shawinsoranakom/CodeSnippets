def test_true(self):
        "The 'View on site' button is displayed if view_on_site is True"
        response = self.client.get(
            reverse("admin:admin_views_city_change", args=(self.c1.pk,))
        )
        content_type_pk = ContentType.objects.get_for_model(Restaurant).pk
        self.assertContains(
            response, reverse("admin:view_on_site", args=(content_type_pk, self.r1.pk))
        )