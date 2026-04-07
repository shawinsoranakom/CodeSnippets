def test_prepopulated_on(self):
        response = self.client.get(reverse("admin:admin_views_prepopulatedpost_add"))
        self.assertContains(response, "&quot;id&quot;: &quot;#id_slug&quot;")
        self.assertContains(
            response, "&quot;dependency_ids&quot;: [&quot;#id_title&quot;]"
        )
        self.assertContains(
            response,
            "&quot;id&quot;: &quot;#id_prepopulatedsubpost_set-0-subslug&quot;",
        )