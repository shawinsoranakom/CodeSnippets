def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_sign=Sign("normal")).first()
        self.assertIsNone(obj.null_sign)