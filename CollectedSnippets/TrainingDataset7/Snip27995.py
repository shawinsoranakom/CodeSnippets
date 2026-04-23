def test_dumping(self):
        for value, serialized in self.test_values:
            with self.subTest(value=value):
                instance = JSONModel(value=value)
                data = serializers.serialize("json", [instance])
                self.assertJSONEqual(data, self.test_data % serialized)