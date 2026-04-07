def test_contained_by(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__contained_by=[1, 2]),
            self.objs[:2],
        )