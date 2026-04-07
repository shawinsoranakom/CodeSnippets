def test_invalid_defer(self):
        msg = "Primary has no field named 'missing'"
        with self.assertRaisesMessage(FieldDoesNotExist, msg):
            list(Primary.objects.defer("missing"))
        with self.assertRaisesMessage(FieldError, "missing"):
            list(Primary.objects.defer("value__missing"))
        msg = "Secondary has no field named 'missing'"
        with self.assertRaisesMessage(FieldDoesNotExist, msg):
            list(Primary.objects.defer("related__missing"))