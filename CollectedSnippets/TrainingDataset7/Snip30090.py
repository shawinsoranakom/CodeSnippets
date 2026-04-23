def test_register_type_handlers_no_db(self):
        """Registering type handlers for the nodb connection does nothing."""
        with connection._nodb_cursor() as cursor:
            register_type_handlers(cursor.db)