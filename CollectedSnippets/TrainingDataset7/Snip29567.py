def test_exact_with_expression(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__exact=[Value(1)]),
            self.objs[:1],
        )