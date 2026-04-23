def test_any_value_not_supported(self):
        message = "ANY_VALUE is not supported on this database backend."
        with self.assertRaisesMessage(NotSupportedError, message):
            Book.objects.aggregate(AnyValue("rating"))