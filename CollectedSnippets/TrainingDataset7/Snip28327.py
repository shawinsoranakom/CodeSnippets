def test_save_blank_null_unique_charfield_saves_null(self):
        form_class = modelform_factory(
            model=NullableUniqueCharFieldModel, fields="__all__"
        )
        empty_value = (
            "" if connection.features.interprets_empty_strings_as_nulls else None
        )
        data = {
            "codename": "",
            "email": "",
            "slug": "",
            "url": "",
        }
        form = form_class(data=data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(form.instance.codename, empty_value)
        self.assertEqual(form.instance.email, empty_value)
        self.assertEqual(form.instance.slug, empty_value)
        self.assertEqual(form.instance.url, empty_value)

        # Save a second form to verify there isn't a unique constraint
        # violation.
        form = form_class(data=data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(form.instance.codename, empty_value)
        self.assertEqual(form.instance.email, empty_value)
        self.assertEqual(form.instance.slug, empty_value)
        self.assertEqual(form.instance.url, empty_value)