def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_abs=Abs("normal")).first()
        self.assertIsNone(obj.null_abs)