def test_nested_key_transform_annotation_expression(self):
        obj = NullableJSONModel.objects.create(
            value={"d": ["e", {"f": "g"}, {"f": "g"}]},
        )
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__d__0__isnull=False)
            .annotate(
                key=F("value__d"),
                chain=F("key__1__f"),
                expr=Cast("key", models.JSONField()),
            )
            .filter(chain=F("expr__2__f")),
            [obj],
        )