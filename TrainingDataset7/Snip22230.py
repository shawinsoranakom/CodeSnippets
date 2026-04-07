def test_loaddata_not_found_fields_ignore(self):
        """
        Test for ticket #9279 -- Ignores entries in
        the serialized data for fields that have been removed
        from the database.
        """
        management.call_command(
            "loaddata",
            "sequence_extra",
            ignore=True,
            verbosity=0,
        )
        self.assertEqual(Animal.specimens.all()[0].name, "Lion")