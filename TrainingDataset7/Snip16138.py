def test_delete_selected_uses_get_deleted_objects(self):
        """The delete_selected action uses ModelAdmin.get_deleted_objects()."""
        book = Book.objects.create(name="Test Book")
        data = {
            ACTION_CHECKBOX_NAME: [book.pk],
            "action": "delete_selected",
            "index": 0,
        }
        response = self.client.post(reverse("admin2:admin_views_book_changelist"), data)
        # BookAdmin.get_deleted_objects() returns custom text.
        self.assertContains(response, "a deletable object")