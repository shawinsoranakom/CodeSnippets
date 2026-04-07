def test_opclasses_and_fields_same_length(self):
        msg = "Index.fields and Index.opclasses must have the same number of elements."
        with self.assertRaisesMessage(ValueError, msg):
            models.Index(
                name="test_opclass",
                fields=["field", "other"],
                opclasses=["jsonb_path_ops"],
            )