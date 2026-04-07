def test_exact(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__exact=[1]), self.objs[:1]
        )