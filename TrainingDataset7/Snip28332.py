def test_extra_field_modelform_factory(self):
        with self.assertRaisesMessage(
            FieldError, "Unknown field(s) (no-field) specified for Person"
        ):
            modelform_factory(Person, fields=["no-field", "name"])