def test_decimal_field_0_decimal_places(self):
        """
        A DecimalField with decimal_places=0 should work (#22272).
        """
        field = models.DecimalField(max_digits=5, decimal_places=0)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.DecimalField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"max_digits": 5, "decimal_places": 0})