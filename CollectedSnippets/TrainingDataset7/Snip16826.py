def test_filter_choices_by_request_user(self):
        """
        Ensure the user can only see their own cars in the foreign key
        dropdown.
        """
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:admin_widgets_cartire_add"))
        self.assertNotContains(response, "BMW M3")
        self.assertContains(response, "Volkswagen Passat")