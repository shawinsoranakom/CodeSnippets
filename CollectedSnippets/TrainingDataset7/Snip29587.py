def test_overlap_values(self):
        qs = NullableIntegerArrayModel.objects.filter(order__lt=3)
        self.assertCountEqual(
            NullableIntegerArrayModel.objects.filter(
                field__overlap=qs.values_list("field"),
            ),
            self.objs[:3],
        )
        self.assertCountEqual(
            NullableIntegerArrayModel.objects.filter(
                field__overlap=qs.values("field"),
            ),
            self.objs[:3],
        )