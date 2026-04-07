def test_literal_annotation_filtering(self):
        all_objects = NullableJSONModel.objects.order_by("id")
        qs = all_objects.annotate(data=Value({"foo": "bar"}, JSONField())).filter(
            data__foo="bar"
        )
        self.assertQuerySetEqual(qs, all_objects)