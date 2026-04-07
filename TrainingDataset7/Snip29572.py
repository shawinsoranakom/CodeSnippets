def test_lt(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__lt=[2]), self.objs[:1]
        )