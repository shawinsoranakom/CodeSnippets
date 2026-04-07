def test_loaddata_raises_error_when_fixture_has_invalid_foreign_key(self):
        """
        Data with nonexistent child key references raises error.
        """
        with self.assertRaisesMessage(IntegrityError, "Problem installing fixture"):
            management.call_command(
                "loaddata",
                "forward_ref_bad_data.json",
                verbosity=0,
            )