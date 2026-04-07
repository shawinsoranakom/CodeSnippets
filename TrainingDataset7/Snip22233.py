def test_loaddata_not_found_fields_ignore_yaml(self):
        management.call_command(
            "loaddata",
            "sequence_extra_yaml",
            ignore=True,
            verbosity=0,
        )
        self.assertEqual(Animal.specimens.all()[0].name, "Cat")