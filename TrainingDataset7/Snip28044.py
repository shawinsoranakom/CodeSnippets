def test_unsupported_negative_lookup(self):
        msg = (
            "Using negative JSON array indices is not supported on this database "
            "backend."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            NullableJSONModel.objects.filter(**{"value__-2": 1}).get()