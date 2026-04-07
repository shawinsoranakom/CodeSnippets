def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_atan=ATan("normal")).first()
        self.assertIsNone(obj.null_atan)