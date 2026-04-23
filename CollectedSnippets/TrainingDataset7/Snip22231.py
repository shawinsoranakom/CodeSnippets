def test_loaddata_not_found_fields_ignore_xml(self):
        """
        Test for ticket #19998 -- Ignore entries in the XML serialized data
        for fields that have been removed from the model definition.
        """
        management.call_command(
            "loaddata",
            "sequence_extra_xml",
            ignore=True,
            verbosity=0,
        )
        self.assertEqual(Animal.specimens.all()[0].name, "Wolf")