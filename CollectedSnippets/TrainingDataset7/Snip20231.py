def test_refresh_from_db_when_default_manager_filters(self):
        """
        Model.refresh_from_db() works for instances hidden by the default
        manager.
        """
        book = Book._base_manager.create(is_published=False)
        Book._base_manager.filter(pk=book.pk).update(title="Hi")
        book.refresh_from_db()
        self.assertEqual(book.title, "Hi")