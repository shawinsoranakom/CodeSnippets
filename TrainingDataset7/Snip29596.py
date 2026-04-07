def test_index_annotation(self):
        qs = NullableIntegerArrayModel.objects.annotate(second=models.F("field__1"))
        self.assertCountEqual(
            qs.values_list("second", flat=True),
            [None, None, None, 3, 30],
        )