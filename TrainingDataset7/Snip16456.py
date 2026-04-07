def test_multiple_fkeys_to_same_instance(self):
        """
        If a deleted object has two relationships pointing to it from
        another object, the other object should still only be listed
        once.
        """
        should_contain = '<li>Plot: <a href="%s">World Peace</a></li>' % reverse(
            "admin:admin_views_plot_change", args=(self.pl2.pk,)
        )
        response = self.client.get(
            reverse("admin:admin_views_villain_delete", args=(self.v2.pk,))
        )
        self.assertContains(response, should_contain, 1)