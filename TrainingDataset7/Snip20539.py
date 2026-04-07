def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_round=Round("normal")).first()
        self.assertIsNone(obj.null_round)