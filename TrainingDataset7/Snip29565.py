def test_exact_null_only_array(self):
        obj = NullableIntegerArrayModel.objects.create(
            field=[None], field_nested=[None, None]
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__exact=[None]), [obj]
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field_nested__exact=[None, None]),
            [obj],
        )