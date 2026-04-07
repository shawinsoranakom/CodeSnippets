def test_isnull_key_or_none(self):
        obj = NullableJSONModel.objects.create(value={"a": None})
        self.assertCountEqual(
            NullableJSONModel.objects.filter(
                Q(value__a__isnull=True) | Q(value__a=None)
            ),
            self.objs[:3] + self.objs[5:] + [obj],
        )