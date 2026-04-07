def test_exact_null_only_nested_array(self):
        obj1 = NullableIntegerArrayModel.objects.create(field_nested=[[None, None]])
        obj2 = NullableIntegerArrayModel.objects.create(
            field_nested=[[None, None], [None, None]],
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field_nested__exact=[[None, None]],
            ),
            [obj1],
        )
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field_nested__exact=[[None, None], [None, None]],
            ),
            [obj2],
        )