def test_index_transform_expression(self):
        expr = RawSQL("string_to_array(%s, ';')", ["1;2"])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field__0=Cast(
                    IndexTransform(1, models.IntegerField, expr),
                    output_field=models.IntegerField(),
                ),
            ),
            self.objs[:1],
        )