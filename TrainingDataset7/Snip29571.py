def test_gt(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__gt=[0]), self.objs[:4]
        )