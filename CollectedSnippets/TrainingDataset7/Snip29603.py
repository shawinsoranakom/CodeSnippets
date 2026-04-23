def test_slice_transform_expression(self):
        expr = RawSQL("string_to_array(%s, ';')", ["9;2;3"])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field__0_2=SliceTransform(2, 3, expr)
            ),
            self.objs[2:3],
        )