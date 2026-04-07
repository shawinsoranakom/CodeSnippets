def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_sqrt=Sqrt("normal")).first()
        self.assertIsNone(obj.null_sqrt)