def test_subtract_temporals(self):
        duration_field = DurationField()
        duration_field_internal_type = duration_field.get_internal_type()
        msg = (
            "This backend does not support %s subtraction."
            % duration_field_internal_type
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            self.ops.subtract_temporals(duration_field_internal_type, None, None)