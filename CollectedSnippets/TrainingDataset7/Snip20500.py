def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_degrees=Degrees("normal")).first()
        self.assertIsNone(obj.null_degrees)