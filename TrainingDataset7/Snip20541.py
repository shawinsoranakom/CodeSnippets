def test_null_with_negative_precision(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_round=Round("normal", -1)).first()
        self.assertIsNone(obj.null_round)