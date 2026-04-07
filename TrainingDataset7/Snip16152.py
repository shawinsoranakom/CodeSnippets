def test_selection_counter(self):
        """The selection counter is there."""
        response = self.client.get(reverse("admin:admin_views_subscriber_changelist"))
        self.assertContains(response, "0 of 2 selected")