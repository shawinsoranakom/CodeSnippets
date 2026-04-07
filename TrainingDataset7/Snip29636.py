def test_deconstruct_args(self):
        field = ArrayField(models.CharField(max_length=20))
        name, path, args, kwargs = field.deconstruct()
        new = ArrayField(*args, **kwargs)
        self.assertEqual(new.base_field.max_length, field.base_field.max_length)