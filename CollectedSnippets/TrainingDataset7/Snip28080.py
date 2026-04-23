def test_cast_with_key_text_transform(self):
        obj = NullableJSONModel.objects.annotate(
            json_data=Cast(Value({"foo": "bar"}, JSONField()), JSONField())
        ).get(pk=self.objs[0].pk, json_data__foo__icontains="bar")
        self.assertEqual(obj, self.objs[0])