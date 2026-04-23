def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_tan=Tan("normal")).first()
        self.assertIsNone(obj.null_tan)