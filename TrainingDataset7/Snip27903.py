def test_database_default_unsupported(self):
        msg = "GeneratedField cannot have a database default."
        with self.assertRaisesMessage(ValueError, msg):
            GeneratedField(
                expression=Lower("name"),
                output_field=CharField(max_length=255),
                db_default="",
                db_persist=False,
            )