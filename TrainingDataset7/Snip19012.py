def test_ignore_conflicts_value_error(self):
        message = "This database backend does not support ignoring conflicts."
        with self.assertRaisesMessage(NotSupportedError, message):
            TwoFields.objects.bulk_create(self.data, ignore_conflicts=True)