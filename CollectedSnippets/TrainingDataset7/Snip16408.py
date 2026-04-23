def test_change_view_without_object_change_permission(self):
        """
        The object should be read-only if the user has permission to view it
        and change objects of that type but not to change the current object.
        """
        change_url = reverse("admin9:admin_views_article_change", args=(self.a1.pk,))
        self.client.force_login(self.viewuser)
        response = self.client.get(change_url)
        self.assertEqual(response.context["title"], "View article")
        self.assertContains(
            response, "<title>- | View article | Django site admin</title>"
        )
        self.assertContains(response, "<h1>View article</h1>")
        self.assertContains(
            response,
            '<a role="button" href="/test_admin/admin9/admin_views/article/" '
            'class="closelink">Close</a>',
        )