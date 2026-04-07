def test_error_message(self):
        """
        Regression for #9011 - error message is correct.
        Change from error to warning for ticket #18213.
        """
        msg = "No fixture data found for 'bad_fixture2'. (File format may be invalid.)"
        with self.assertWarnsMessage(RuntimeWarning, msg):
            management.call_command(
                "loaddata",
                "bad_fixture2",
                "animal",
                verbosity=0,
            )