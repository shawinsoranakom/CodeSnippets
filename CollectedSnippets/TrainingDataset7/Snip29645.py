def test_unbounded(self):
        field = ArrayField(models.IntegerField())
        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean([1, None], None)
        self.assertEqual(cm.exception.code, "item_invalid")
        self.assertEqual(
            cm.exception.message % cm.exception.params,
            "Item 2 in the array did not validate: This field cannot be null.",
        )