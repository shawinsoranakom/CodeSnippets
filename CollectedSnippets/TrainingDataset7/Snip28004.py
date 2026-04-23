def test_bulk_update_custom_get_prep_value(self):
        obj = CustomSerializationJSONModel.objects.create(json_field={"version": "1"})
        obj.json_field["version"] = "1-alpha"
        CustomSerializationJSONModel.objects.bulk_update([obj], ["json_field"])
        self.assertSequenceEqual(
            CustomSerializationJSONModel.objects.values("json_field"),
            [{"json_field": '{"version": "1-alpha"}'}],
        )