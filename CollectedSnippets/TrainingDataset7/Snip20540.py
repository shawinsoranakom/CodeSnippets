def test_null_with_precision(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_round=Round("normal", 5)).first()
        self.assertIsNone(obj.null_round)