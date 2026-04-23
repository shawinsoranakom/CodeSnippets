def test_loaddata_empty_lines_jsonl(self):
        management.call_command(
            "loaddata",
            "sequence_empty_lines_jsonl.jsonl",
            verbosity=0,
        )
        self.assertEqual(Animal.specimens.all()[0].name, "Eagle")