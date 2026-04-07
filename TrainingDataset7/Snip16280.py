def test_basic_edit_GET_string_PK(self):
        """
        GET on the change_view (when passing a string as the PK argument for a
        model with an integer PK field) redirects to the index page with a
        message saying the object doesn't exist.
        """
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(quote("abc/<b>"),)),
            follow=True,
        )
        self.assertRedirects(response, reverse("admin:index"))
        self.assertEqual(
            [m.message for m in response.context["messages"]],
            ["section with ID “abc/<b>” doesn’t exist. Perhaps it was deleted?"],
        )