def test_nested_json_object_array(self):
        obj = Author.objects.annotate(
            json_object=JSONObject(
                name="name",
                nested_json_array=JSONArray(
                    JSONObject(alias1="alias", age1="age"),
                    JSONObject(alias2="alias", age2="age"),
                ),
            )
        ).first()
        self.assertEqual(
            obj.json_object,
            {
                "name": "Ivan Ivanov",
                "nested_json_array": [
                    {"alias1": "iivanov", "age1": 30},
                    {"alias2": "iivanov", "age2": 30},
                ],
            },
        )