def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_cot=Cot("normal")).first()
        self.assertIsNone(obj.null_cot)