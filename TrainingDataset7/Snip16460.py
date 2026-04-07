def test_delete_view_uses_get_deleted_objects(self):
        """The delete view uses ModelAdmin.get_deleted_objects()."""
        book = Book.objects.create(name="Test Book")
        response = self.client.get(
            reverse("admin2:admin_views_book_delete", args=(book.pk,))
        )
        # BookAdmin.get_deleted_objects() returns custom text.
        self.assertContains(response, "a deletable object")