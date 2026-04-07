def test_dumping(self):
        for field_value, array_field_value in self.field_values:
            with self.subTest(field_value=field_value, array_value=array_field_value):
                instance = HStoreModel(field=field_value, array_field=array_field_value)
                data = serializers.serialize("json", [instance])
                json_data = self.create_json_data(field_value, array_field_value)
                self.assertEqual(json.loads(data), json.loads(json_data))