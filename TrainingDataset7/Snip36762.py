def assertFailsValidation(self, clean, failed_fields, **kwargs):
        with self.assertRaises(ValidationError) as cm:
            clean(**kwargs)
        self.assertEqual(sorted(failed_fields), sorted(cm.exception.message_dict))