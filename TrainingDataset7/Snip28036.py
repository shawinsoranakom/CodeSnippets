def test_deep_values(self):
        qs = NullableJSONModel.objects.values_list("value__k__l").order_by("pk")
        expected_objs = [(None,)] * len(self.objs)
        expected_objs[4] = ("m",)
        self.assertSequenceEqual(qs, expected_objs)