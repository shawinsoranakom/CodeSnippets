def test_invalid_data_no_ext(self):
        """
        Test for ticket #4371 -- Loading a fixture file with invalid data
        without file extension.
        Test for ticket #18213 -- warning conditions are caught correctly
        """
        msg = "No fixture data found for 'bad_fixture2'. (File format may be invalid.)"
        with self.assertWarnsMessage(RuntimeWarning, msg):
            management.call_command(
                "loaddata",
                "bad_fixture2",
                verbosity=0,
            )