def test_server_side_cursors_setting(self):
        with self.override_db_setting(DISABLE_SERVER_SIDE_CURSORS=False):
            persons = Person.objects.iterator()
            self.assertUsesCursor(persons)
            del persons  # Close server-side cursor

        # On PyPy, the cursor is left open here and attempting to force garbage
        # collection breaks the transaction wrapping the test.
        with self.override_db_setting(DISABLE_SERVER_SIDE_CURSORS=True):
            self.assertNotUsesCursor(Person.objects.iterator())