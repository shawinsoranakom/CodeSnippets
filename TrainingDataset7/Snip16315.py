def test_incorrect_lookup_parameters(self):
        """Ensure incorrect lookup parameters are handled gracefully."""
        changelist_url = reverse("admin:admin_views_thing_changelist")
        response = self.client.get(changelist_url, {"notarealfield": "5"})
        self.assertRedirects(response, "%s?e=1" % changelist_url)

        # Spanning relationships through a nonexistent related object (Refs
        # #16716)
        response = self.client.get(changelist_url, {"notarealfield__whatever": "5"})
        self.assertRedirects(response, "%s?e=1" % changelist_url)

        response = self.client.get(
            changelist_url, {"color__id__exact": "StringNotInteger!"}
        )
        self.assertRedirects(response, "%s?e=1" % changelist_url)

        # Regression test for #18530
        response = self.client.get(changelist_url, {"pub_date__gte": "foo"})
        self.assertRedirects(response, "%s?e=1" % changelist_url)