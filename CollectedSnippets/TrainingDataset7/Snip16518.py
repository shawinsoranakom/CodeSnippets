def test_custom_changelist(self):
        """
        Validate that a custom ChangeList class can be used (#9749)
        """
        # Insert some data
        post_data = {"name": "First Gadget"}
        response = self.client.post(reverse("admin:admin_views_gadget_add"), post_data)
        self.assertEqual(response.status_code, 302)  # redirect somewhere
        # Hit the page once to get messages out of the queue message list
        response = self.client.get(reverse("admin:admin_views_gadget_changelist"))
        # Data is still not visible on the page
        response = self.client.get(reverse("admin:admin_views_gadget_changelist"))
        self.assertNotContains(response, "First Gadget")