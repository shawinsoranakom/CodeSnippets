def test_validate_fields_generated_field_stored(self):
        self.assertGeneratedFieldWithFieldsIsValidated(
            model=GeneratedFieldStoredProduct
        )