def test_validate_fields_generated_field_stored_nulls_distinct(self):
        self.assertGeneratedFieldNullsDistinctIsValidated(
            model=GeneratedFieldStoredProduct
        )