def test_nested_key_transform_on_subquery(self):
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__d__0__isnull=False)
            .annotate(
                subquery_value=Subquery(
                    NullableJSONModel.objects.filter(pk=OuterRef("pk")).values("value")
                ),
                key=KeyTransform("d", "subquery_value"),
                chain=KeyTransform("f", KeyTransform("1", "key")),
            )
            .filter(chain="g"),
            [self.objs[4]],
        )