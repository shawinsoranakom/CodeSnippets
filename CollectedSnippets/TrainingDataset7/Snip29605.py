def test_slicing_of_f_expressions(self):
        tests = [
            (F("field")[:2], [1, 2]),
            (F("field")[2:], [3, 4]),
            (F("field")[1:3], [2, 3]),
            (F("field")[3], [4]),
            (F("field")[:3][1:], [2, 3]),  # Nested slicing.
            (F("field")[:3][1], [2]),  # Slice then index.
        ]
        for expression, expected in tests:
            with self.subTest(expression=expression, expected=expected):
                instance = IntegerArrayModel.objects.create(field=[1, 2, 3, 4])
                instance.field = expression
                instance.save()
                instance.refresh_from_db()
                self.assertEqual(instance.field, expected)