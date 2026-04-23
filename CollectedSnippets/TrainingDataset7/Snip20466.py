def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_acos=ACos("normal")).first()
        self.assertIsNone(obj.null_acos)