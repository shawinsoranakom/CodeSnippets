def test_csi_field(self):
        field = models.CommaSeparatedIntegerField(max_length=100)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.CommaSeparatedIntegerField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"max_length": 100})