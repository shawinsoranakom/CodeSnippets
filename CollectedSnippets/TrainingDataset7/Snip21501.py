def test_resolve_output_field(self):
        value_types = [
            ("str", CharField),
            (True, BooleanField),
            (42, IntegerField),
            (3.14, FloatField),
            (datetime.date(2019, 5, 15), DateField),
            (datetime.datetime(2019, 5, 15), DateTimeField),
            (datetime.time(3, 16), TimeField),
            (datetime.timedelta(1), DurationField),
            (Decimal("3.14"), DecimalField),
            (b"", BinaryField),
            (uuid.uuid4(), UUIDField),
        ]
        for value, output_field_type in value_types:
            with self.subTest(type=type(value)):
                expr = Value(value)
                self.assertIsInstance(expr.output_field, output_field_type)