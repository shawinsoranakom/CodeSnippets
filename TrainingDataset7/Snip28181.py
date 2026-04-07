def test_filter_with_expr(self):
        self.assertSequenceEqualWithoutHyphens(
            NullableUUIDModel.objects.annotate(
                value=Concat(Value("8400"), Value("e29b"), output_field=CharField()),
            ).filter(field__contains=F("value")),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.annotate(
                value=Concat(
                    Value("8400"), Value("-"), Value("e29b"), output_field=CharField()
                ),
            ).filter(field__contains=F("value")),
            [self.objs[1]],
        )
        self.assertSequenceEqual(
            NullableUUIDModel.objects.annotate(
                value=Repeat(Value("0"), 4, output_field=CharField()),
            ).filter(field__contains=F("value")),
            [self.objs[1]],
        )