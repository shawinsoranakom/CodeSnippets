def test_validate_fields_generated_field_virtual(self):
        self.assertGeneratedFieldWithFieldsIsValidated(
            model=GeneratedFieldVirtualProduct
        )