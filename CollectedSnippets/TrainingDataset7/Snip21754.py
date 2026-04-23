def test_ip_address_field(self):
        field = models.IPAddressField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.IPAddressField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})