def test_invalid_uuid(self):
        field = models.UUIDField()
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean("550e8400", None)
        self.assertEqual(cm.exception.code, "invalid")
        self.assertEqual(
            cm.exception.message % cm.exception.params,
            "“550e8400” is not a valid UUID.",
        )