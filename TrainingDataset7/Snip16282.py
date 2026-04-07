def test_basic_inheritance_GET_string_PK(self):
        """
        GET on the change_view (for inherited models) redirects to the index
        page with a message saying the object doesn't exist.
        """
        response = self.client.get(
            reverse("admin:admin_views_supervillain_change", args=("abc",)), follow=True
        )
        self.assertRedirects(response, reverse("admin:index"))
        self.assertEqual(
            [m.message for m in response.context["messages"]],
            ["super villain with ID “abc” doesn’t exist. Perhaps it was deleted?"],
        )