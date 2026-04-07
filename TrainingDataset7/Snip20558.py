def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_sin=Sin("normal")).first()
        self.assertIsNone(obj.null_sin)