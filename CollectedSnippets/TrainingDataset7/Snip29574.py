def test_in_subquery(self):
        IntegerArrayModel.objects.create(field=[2, 3])
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(
                field__in=IntegerArrayModel.objects.values_list("field", flat=True)
            ),
            self.objs[2:3],
        )