def test_invalid_value(self):
        msg = "is not JSON serializable"
        with self.assertRaisesMessage(TypeError, msg):
            NullableJSONModel.objects.create(
                value={
                    "uuid": uuid.UUID("d85e2076-b67c-4ee7-8c3a-2bf5a2cc2475"),
                }
            )