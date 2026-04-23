def test_has_key(self):
        self.assertCountEqual(
            NullableJSONModel.objects.filter(value__has_key="a"),
            [self.objs[3], self.objs[4]],
        )