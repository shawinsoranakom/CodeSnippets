def test_related_invalid_field_type_stored_generated_field(self):
        self.assertGeneratedIntegerFieldIsInvalid(db_persist=True)