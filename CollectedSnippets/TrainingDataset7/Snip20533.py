def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_radians=Radians("normal")).first()
        self.assertIsNone(obj.null_radians)