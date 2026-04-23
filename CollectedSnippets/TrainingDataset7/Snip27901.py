def test_blank_unsupported(self):
        with self.assertRaisesMessage(ValueError, "GeneratedField must be blank."):
            GeneratedField(
                expression=Lower("name"),
                output_field=CharField(max_length=255),
                blank=False,
                db_persist=False,
            )