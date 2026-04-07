def test_reset_link(self):
        """
        Test presence of reset link in search bar ("1 result (_x total_)").
        """
        #   1 query for session + 1 for fetching user
        # + 1 for filtered result + 1 for filtered count
        # + 1 for total count
        with self.assertNumQueries(5):
            response = self.client.get(
                reverse("admin:admin_views_person_changelist") + "?q=Gui"
            )
        self.assertContains(
            response,
            """<span class="small quiet">1 result (<a href="?">6 total</a>)</span>""",
            html=True,
        )