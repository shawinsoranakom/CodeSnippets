def test_loaddata_error_message(self):
        """
        Loading a fixture which contains an invalid object outputs an error
        message which contains the pk of the object that triggered the error.
        """
        # MySQL needs a little prodding to reject invalid data.
        # This won't affect other tests because the database connection
        # is closed at the end of each test.
        if connection.vendor == "mysql":
            with connection.cursor() as cursor:
                cursor.execute("SET sql_mode = 'TRADITIONAL'")
        msg = "Could not load fixtures.Article(pk=1):"
        with self.assertRaisesMessage(IntegrityError, msg):
            management.call_command("loaddata", "invalid.json", verbosity=0)