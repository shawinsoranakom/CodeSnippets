def test_null(self):
        IntegerModel.objects.create()
        obj = IntegerModel.objects.annotate(null_asin=ASin("normal")).first()
        self.assertIsNone(obj.null_asin)