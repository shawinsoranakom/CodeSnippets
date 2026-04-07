def test_is_usable_after_database_disconnects(self):
        """
        is_usable() doesn't crash when the database disconnects (#21553).
        """
        # Open a connection to the database.
        with connection.cursor():
            pass
        # Emulate a connection close by the database.
        connection._close()
        # Even then is_usable() should not raise an exception.
        try:
            self.assertFalse(connection.is_usable())
        finally:
            # Clean up the mess created by connection._close(). Since the
            # connection is already closed, this crashes on some backends.
            try:
                connection.close()
            except Exception:
                pass