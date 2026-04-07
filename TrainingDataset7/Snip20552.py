def test_unsupported_negative_precision(self):
        FloatModel.objects.create(f1=123.45)
        msg = "SQLite does not support negative precision."
        with self.assertRaisesMessage(ValueError, msg):
            FloatModel.objects.annotate(value=Round("f1", -1)).first()