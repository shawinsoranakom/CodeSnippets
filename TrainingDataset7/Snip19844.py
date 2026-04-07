def test_validate_fields_generated_field_virtual_nulls_distinct(self):
        self.assertGeneratedFieldNullsDistinctIsValidated(
            model=GeneratedFieldVirtualProduct
        )