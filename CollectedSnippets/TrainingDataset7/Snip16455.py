def test_multiple_fkeys_to_same_model(self):
        """
        If a deleted object has two relationships from another model,
        both of those should be followed in looking for related
        objects to delete.
        """
        should_contain = '<li>Plot: <a href="%s">World Domination</a>' % reverse(
            "admin:admin_views_plot_change", args=(self.pl1.pk,)
        )
        response = self.client.get(
            reverse("admin:admin_views_villain_delete", args=(self.v1.pk,))
        )
        self.assertContains(response, should_contain)
        response = self.client.get(
            reverse("admin:admin_views_villain_delete", args=(self.v2.pk,))
        )
        self.assertContains(response, should_contain)