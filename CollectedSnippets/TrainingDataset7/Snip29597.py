def test_overlap(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__overlap=[1, 2]),
            self.objs[0:3],
        )