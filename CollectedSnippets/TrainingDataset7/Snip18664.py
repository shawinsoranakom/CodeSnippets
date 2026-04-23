def test_nodb_cursor_reraise_exceptions(self):
        with self.assertRaisesMessage(DatabaseError, "exception"):
            with connection._nodb_cursor():
                raise DatabaseError("exception")