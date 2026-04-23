def test_related_invalid_field_type_virtual_generated_field(self):
        self.assertGeneratedIntegerFieldIsInvalid(db_persist=False)