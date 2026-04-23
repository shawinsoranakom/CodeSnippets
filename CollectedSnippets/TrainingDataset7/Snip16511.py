def test_no_total_count(self):
        """
        #8408 -- "Show all" should be displayed instead of the total count if
        ModelAdmin.show_full_result_count is False.
        """
        #   1 query for session + 1 for fetching user
        # + 1 for filtered result + 1 for filtered count
        with self.assertNumQueries(4):
            response = self.client.get(
                reverse("admin:admin_views_recommendation_changelist") + "?q=bar"
            )
        self.assertContains(
            response,
            """<span class="small quiet">1 result (<a href="?">Show all</a>)</span>""",
            html=True,
        )
        self.assertTrue(response.context["cl"].show_admin_actions)