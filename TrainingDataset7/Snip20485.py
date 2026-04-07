def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_ceil=Ceil("normal")).first()
        self.assertIsNone(obj.null_ceil)