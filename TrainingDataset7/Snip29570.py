def test_isnull(self):
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__isnull=True), self.objs[-1:]
        )