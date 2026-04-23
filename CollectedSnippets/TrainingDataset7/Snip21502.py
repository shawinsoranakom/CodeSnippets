def test_resolve_output_field_failure(self):
        msg = "Cannot resolve expression type, unknown output_field"
        with self.assertRaisesMessage(FieldError, msg):
            Value(object()).output_field