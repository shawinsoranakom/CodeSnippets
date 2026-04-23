def test_delete_cursor_rowcount(self):
        """
        The rowcount attribute should not be checked on a closed cursor.
        """

        class MockedCursorWrapper(CursorWrapper):
            is_closed = False

            def close(self):
                self.cursor.close()
                self.is_closed = True

            @property
            def rowcount(self):
                if self.is_closed:
                    raise Exception("Cursor is closed.")
                return self.cursor.rowcount

        cache.set_many({"a": 1, "b": 2})
        with mock.patch("django.db.backends.utils.CursorWrapper", MockedCursorWrapper):
            self.assertIs(cache.delete("a"), True)