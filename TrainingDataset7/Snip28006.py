def test_exact(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__exact={}),
            [self.objs[2]],
        )