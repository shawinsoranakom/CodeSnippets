def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_cos=Cos("normal")).first()
        self.assertIsNone(obj.null_cos)