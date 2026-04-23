def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_exp=Exp("normal")).first()
        self.assertIsNone(obj.null_exp)