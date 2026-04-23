def test_serialize_callable_choices(self):
        field = models.IntegerField(choices=get_choices)
        string = MigrationWriter.serialize(field)[0]
        self.assertEqual(
            string,
            "models.IntegerField(choices=migrations.test_writer.get_choices)",
        )