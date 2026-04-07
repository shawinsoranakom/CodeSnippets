def test_unicode_delete(self):
        """
        The delete_view handles non-ASCII characters
        """
        delete_dict = {"post": "yes"}
        delete_url = reverse("admin:admin_views_book_delete", args=(self.b1.pk,))
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(delete_url, delete_dict)
        self.assertRedirects(response, reverse("admin:admin_views_book_changelist"))