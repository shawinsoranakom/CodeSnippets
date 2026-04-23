def test_deconstruct(self):
        field = ArrayField(models.IntegerField())
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(kwargs.keys(), {"base_field"})
        new = ArrayField(*args, **kwargs)
        self.assertEqual(type(new.base_field), type(field.base_field))
        self.assertIsNot(new.base_field, field.base_field)