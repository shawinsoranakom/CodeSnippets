def test_has_key_literal_lookup(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(
                HasKey(Value({"foo": "bar"}, JSONField()), "foo")
            ).order_by("id"),
            self.objs,
        )