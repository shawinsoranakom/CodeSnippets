def test_invalid_data(self):
        """
        Test for ticket #4371 -- Loading a fixture file with invalid data
        using explicit filename.
        Test for ticket #18213 -- warning conditions are caught correctly
        """
        msg = "No fixture data found for 'bad_fixture2'. (File format may be invalid.)"
        with self.assertWarnsMessage(RuntimeWarning, msg):
            management.call_command(
                "loaddata",
                "bad_fixture2.xml",
                verbosity=0,
            )