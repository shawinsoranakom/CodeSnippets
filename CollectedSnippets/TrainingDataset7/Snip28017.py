def test_key_transform_annotation_expression(self):
        obj = NullableJSONModel.objects.create(value={"d": ["e", "e"]})
        self.assertSequenceEqual(
            NullableJSONModel.objects.filter(value__d__0__isnull=False)
            .annotate(
                key=F("value__d"),
                chain=F("key__0"),
                expr=Cast("key", models.JSONField()),
            )
            .filter(chain=F("expr__1")),
            [obj],
        )