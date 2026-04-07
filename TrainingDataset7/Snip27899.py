def test_editable_unsupported(self):
        with self.assertRaisesMessage(ValueError, "GeneratedField cannot be editable."):
            GeneratedField(
                expression=Lower("name"),
                output_field=CharField(max_length=255),
                editable=True,
                db_persist=False,
            )