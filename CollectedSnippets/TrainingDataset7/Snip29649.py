def test_nested_array_mismatch(self):
        field = ArrayField(ArrayField(models.IntegerField()))
        field.clean([[1, 2], [3, 4]], None)
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean([[1, 2], [3, 4, 5]], None)
        self.assertEqual(cm.exception.code, "nested_array_mismatch")
        self.assertEqual(
            cm.exception.messages[0], "Nested arrays must have the same length."
        )