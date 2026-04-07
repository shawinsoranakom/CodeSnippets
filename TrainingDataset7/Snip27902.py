def test_default_unsupported(self):
        msg = "GeneratedField cannot have a default."
        with self.assertRaisesMessage(ValueError, msg):
            GeneratedField(
                expression=Lower("name"),
                output_field=CharField(max_length=255),
                default="",
                db_persist=False,
            )