def test_has_any_keys(self):
        self.assertCountEqual(
            NullableJSONModel.objects.filter(value__has_any_keys=["c", "l"]),
            [self.objs[3], self.objs[4], self.objs[6]],
        )