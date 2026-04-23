def test_slicing_of_f_expressions_with_len(self):
        queryset = NullableIntegerArrayModel.objects.annotate(
            subarray=F("field")[:1]
        ).filter(field__len=F("subarray__len"))
        self.assertSequenceEqual(queryset, self.objs[:2])