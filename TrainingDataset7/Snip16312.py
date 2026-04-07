def test_limited_filter(self):
        """
        Admin changelist filters do not contain objects excluded via
        limit_choices_to.
        """
        response = self.client.get(reverse("admin:admin_views_thing_changelist"))
        self.assertContains(
            response,
            '<search id="changelist-filter" '
            'aria-labelledby="changelist-filter-header">',
            msg_prefix="Expected filter not found in changelist view",
        )
        self.assertNotContains(
            response,
            '<a href="?color__id__exact=3">Blue</a>',
            msg_prefix="Changelist filter not correctly limited by limit_choices_to",
        )