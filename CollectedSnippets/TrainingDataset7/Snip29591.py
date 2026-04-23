def test_index(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0=2), self.objs[1:3]
        )