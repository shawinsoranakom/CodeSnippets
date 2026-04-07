def test_empty(self):
        """
        Test for ticket #18213 -- Loading a fixture file with no data output a
        warning. Previously empty fixture raises an error exception, see ticket
        #4371.
        """
        msg = "No fixture data found for 'empty'. (File format may be invalid.)"
        with self.assertWarnsMessage(RuntimeWarning, msg):
            management.call_command(
                "loaddata",
                "empty",
                verbosity=0,
            )