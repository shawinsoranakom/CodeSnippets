def test_history_view_custom_qs(self):
        """
        Custom querysets are considered for the admin history view.
        """
        self.client.post(reverse("admin:login"), self.super_login)
        FilteredManager.objects.create(pk=1)
        FilteredManager.objects.create(pk=2)
        response = self.client.get(
            reverse("admin:admin_views_filteredmanager_changelist")
        )
        self.assertContains(response, "PK=1")
        self.assertContains(response, "PK=2")
        self.assertEqual(
            self.client.get(
                reverse("admin:admin_views_filteredmanager_history", args=(1,))
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("admin:admin_views_filteredmanager_history", args=(2,))
            ).status_code,
            200,
        )