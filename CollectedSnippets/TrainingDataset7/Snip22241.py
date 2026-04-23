def test_unknown_format(self):
        """
        Test for ticket #4371 -- Loading data of an unknown format should fail
        Validate that error conditions are caught correctly
        """
        msg = (
            "Problem installing fixture 'bad_fix.ture1': unkn is not a known "
            "serialization format."
        )
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command(
                "loaddata",
                "bad_fix.ture1.unkn",
                verbosity=0,
            )