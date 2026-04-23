def assertFieldFailsValidationWithMessage(self, clean, field_name, message):
        with self.assertRaises(ValidationError) as cm:
            clean()
        self.assertIn(field_name, cm.exception.message_dict)
        self.assertEqual(message, cm.exception.message_dict[field_name])