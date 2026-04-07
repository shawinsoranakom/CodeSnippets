def test_search_on_sibling_models(self):
        "A search that mentions sibling models"
        response = self.client.get(
            reverse("admin:admin_views_recommendation_changelist") + "?q=bar"
        )
        # confirm the search returned 1 object
        self.assertContains(response, "\n1 recommendation\n")