def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_floor=Floor("normal")).first()
        self.assertIsNone(obj.null_floor)