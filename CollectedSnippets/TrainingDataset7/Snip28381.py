def test_explicitpk_unique(self):
        """
        Ensure keys and blank character strings are tested for uniqueness.
        """
        form = ExplicitPKForm({"key": "key1", "desc": ""})
        self.assertTrue(form.is_valid())
        form.save()
        form = ExplicitPKForm({"key": "key1", "desc": ""})
        self.assertFalse(form.is_valid())
        if connection.features.interprets_empty_strings_as_nulls:
            self.assertEqual(len(form.errors), 1)
            self.assertEqual(
                form.errors["key"], ["Explicit pk with this Key already exists."]
            )
        else:
            self.assertEqual(len(form.errors), 3)
            self.assertEqual(
                form.errors["__all__"],
                ["Explicit pk with this Key and Desc already exists."],
            )
            self.assertEqual(
                form.errors["desc"], ["Explicit pk with this Desc already exists."]
            )
            self.assertEqual(
                form.errors["key"], ["Explicit pk with this Key already exists."]
            )