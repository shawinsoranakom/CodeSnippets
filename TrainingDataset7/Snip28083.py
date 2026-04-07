def test_key_text_transform_from_lookup(self):
        qs = NullableJSONModel.objects.annotate(b=KT("value__bax__foo")).filter(
            b__contains="ar",
        )
        self.assertSequenceEqual(qs, [self.objs[7]])
        qs = NullableJSONModel.objects.annotate(c=KT("value__o")).filter(
            c__contains="uot",
        )
        self.assertSequenceEqual(qs, [self.objs[4]])