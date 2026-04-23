def test_prepopulated_off(self):
        response = self.client.get(
            reverse("admin:admin_views_prepopulatedpost_change", args=(self.p1.pk,))
        )
        self.assertContains(response, "A Long Title")
        self.assertNotContains(response, "&quot;id&quot;: &quot;#id_slug&quot;")
        self.assertNotContains(
            response, "&quot;dependency_ids&quot;: [&quot;#id_title&quot;]"
        )
        self.assertNotContains(
            response,
            "&quot;id&quot;: &quot;#id_prepopulatedsubpost_set-0-subslug&quot;",
        )