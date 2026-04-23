def test_icontains(self):
        self.assertCountEqual(
            NullableJSONModel.objects.filter(value__icontains="BaX"),
            self.objs[6:8],
        )