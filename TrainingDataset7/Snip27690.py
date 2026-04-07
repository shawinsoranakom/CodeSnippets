def test_serialize_dictionary_choices(self):
        for choices in ({"Group": [(2, "2"), (1, "1")]}, {"Group": {2: "2", 1: "1"}}):
            with self.subTest(choices):
                field = models.IntegerField(choices=choices)
                string = MigrationWriter.serialize(field)[0]
                self.assertEqual(
                    string,
                    "models.IntegerField(choices=[('Group', [(2, '2'), (1, '1')])])",
                )