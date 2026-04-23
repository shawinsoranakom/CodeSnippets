def test_len(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__len__lte=2), self.objs[0:3]
        )