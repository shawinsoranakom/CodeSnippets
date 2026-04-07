def test_change_list_facet_toggle(self):
        # Toggle is visible when show_facet is the default of
        # admin.ShowFacets.ALLOW.
        admin_url = reverse("admin:admin_views_album_changelist")
        response = self.client.get(admin_url)
        self.assertContains(
            response,
            '<a href="?_facets=True" class="viewlink">Show counts</a>',
            msg_prefix="Expected facet filter toggle not found in changelist view",
        )
        response = self.client.get(f"{admin_url}?_facets=True")
        self.assertContains(
            response,
            '<a href="?" class="hidelink">Hide counts</a>',
            msg_prefix="Expected facet filter toggle not found in changelist view",
        )
        # Toggle is not visible when show_facet is admin.ShowFacets.ALWAYS.
        response = self.client.get(reverse("admin:admin_views_workhour_changelist"))
        self.assertNotContains(
            response,
            "Show counts",
            msg_prefix="Expected not to find facet filter toggle in changelist view",
        )
        self.assertNotContains(
            response,
            "Hide counts",
            msg_prefix="Expected not to find facet filter toggle in changelist view",
        )
        # Toggle is not visible when show_facet is admin.ShowFacets.NEVER.
        response = self.client.get(reverse("admin:admin_views_fooddelivery_changelist"))
        self.assertNotContains(
            response,
            "Show counts",
            msg_prefix="Expected not to find facet filter toggle in changelist view",
        )
        self.assertNotContains(
            response,
            "Hide counts",
            msg_prefix="Expected not to find facet filter toggle in changelist view",
        )