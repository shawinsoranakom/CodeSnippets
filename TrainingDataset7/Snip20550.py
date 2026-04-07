def test_integer_with_negative_precision(self):
        IntegerModel.objects.create(normal=365)
        obj = IntegerModel.objects.annotate(normal_round=Round("normal", -1)).first()
        self.assertIsInstance(obj.normal_round, int)
        expected = 360 if connection.features.rounds_to_even else 370
        self.assertEqual(obj.normal_round, expected)