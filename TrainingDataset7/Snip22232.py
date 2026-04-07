def test_loaddata_not_found_fields_ignore_jsonl(self):
        management.call_command(
            "loaddata",
            "sequence_extra_jsonl",
            ignore=True,
            verbosity=0,
        )
        self.assertEqual(Animal.specimens.all()[0].name, "Eagle")