def test_deconstruct(self):
        field = models.UUIDField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(kwargs, {})