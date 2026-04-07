def test_null(self):
        IntegerModel.objects.create(big=100)
        obj = IntegerModel.objects.annotate(
            null_atan2_sn=ATan2("small", "normal"),
            null_atan2_nb=ATan2("normal", "big"),
            null_atan2_bn=ATan2("big", "normal"),
        ).first()
        self.assertIsNone(obj.null_atan2_sn)
        self.assertIsNone(obj.null_atan2_nb)
        self.assertIsNone(obj.null_atan2_bn)