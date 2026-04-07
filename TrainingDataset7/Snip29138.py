def test_refresh_router_instance_hint(self):
        router = Mock()
        router.db_for_read.return_value = None
        book = Book.objects.create(
            title="Dive Into Python", published=datetime.date(1957, 10, 12)
        )
        with self.settings(DATABASE_ROUTERS=[router]):
            book.refresh_from_db()
        router.db_for_read.assert_called_once_with(Book, instance=book)