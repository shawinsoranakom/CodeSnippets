def test_change_view(self):
        for i in self.pks:
            url = reverse("admin:admin_views_emptymodel_change", args=(i,))
            response = self.client.get(url, follow=True)
            if i > 1:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertRedirects(response, reverse("admin:index"))
                self.assertEqual(
                    [m.message for m in response.context["messages"]],
                    ["empty model with ID “1” doesn’t exist. Perhaps it was deleted?"],
                )