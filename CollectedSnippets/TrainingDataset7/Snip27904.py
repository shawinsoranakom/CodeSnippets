def test_db_persist_required(self):
        with self.assertRaises(TypeError):
            GeneratedField(
                expression=Lower("name"), output_field=CharField(max_length=255)
            )
        msg = "GeneratedField.db_persist must be True or False."
        with self.assertRaisesMessage(ValueError, msg):
            GeneratedField(
                expression=Lower("name"),
                output_field=CharField(max_length=255),
                db_persist=None,
            )