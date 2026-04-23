def test_shallow_obj_lookup(self):
        self.assertCountEqual(
            NullableJSONModel.objects.filter(value__a="b"),
            [self.objs[3], self.objs[4]],
        )