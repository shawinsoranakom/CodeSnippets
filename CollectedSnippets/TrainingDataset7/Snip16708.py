def test_delete_view(self):
        # Test redirect on "Delete".
        response = self.client.post(self.get_delete_url(), {"post": "yes"})
        self.assertRedirects(response, self.get_changelist_url())