def test_exact_matches(self):
        response = self.client.get(
            reverse("admin:admin_views_recommendation_changelist") + "?q=bar"
        )
        # confirm the search returned one object
        self.assertContains(response, "\n1 recommendation\n")

        response = self.client.get(
            reverse("admin:admin_views_recommendation_changelist") + "?q=ba"
        )
        # confirm the search returned zero objects
        self.assertContains(response, "\n0 recommendations\n")