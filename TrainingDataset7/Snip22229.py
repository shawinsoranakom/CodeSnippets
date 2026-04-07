def test_loaddata_not_found_fields_not_ignore(self):
        """
        Test for ticket #9279 -- Error is raised for entries in
        the serialized data for fields that have been removed
        from the database when not ignored.
        """
        test_fixtures = [
            "sequence_extra",
            "sequence_extra_jsonl",
        ]
        if HAS_YAML:
            test_fixtures.append("sequence_extra_yaml")
        for fixture_file in test_fixtures:
            with (
                self.subTest(fixture_file=fixture_file),
                self.assertRaises(DeserializationError),
            ):
                management.call_command(
                    "loaddata",
                    fixture_file,
                    verbosity=0,
                )