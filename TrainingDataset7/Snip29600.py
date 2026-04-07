def test_slice(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0_1=[2]), self.objs[1:3]
        )

        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__0_2=[2, 3]), self.objs[2:3]
        )