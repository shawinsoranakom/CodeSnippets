def test_key_text_transform_char_lookup(self):
        qs = NullableJSONModel.objects.annotate(
            char_value=KeyTextTransform("foo", "value"),
        ).filter(char_value__startswith="bar")
        self.assertSequenceEqual(qs, [self.objs[7]])

        qs = NullableJSONModel.objects.annotate(
            char_value=KeyTextTransform(1, KeyTextTransform("bar", "value")),
        ).filter(char_value__startswith="bar")
        self.assertSequenceEqual(qs, [self.objs[7]])