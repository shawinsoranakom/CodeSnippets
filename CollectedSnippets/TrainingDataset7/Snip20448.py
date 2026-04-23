def test_nested_json_array_object(self):
        obj = Author.objects.annotate(
            json_array=JSONArray(
                JSONObject(
                    name1="name",
                    nested_json_object1=JSONObject(alias1="alias", age1="age"),
                ),
                JSONObject(
                    name2="name",
                    nested_json_object2=JSONObject(alias2="alias", age2="age"),
                ),
            )
        ).first()
        self.assertEqual(
            obj.json_array,
            [
                {
                    "name1": "Ivan Ivanov",
                    "nested_json_object1": {"alias1": "iivanov", "age1": 30},
                },
                {
                    "name2": "Ivan Ivanov",
                    "nested_json_object2": {"alias2": "iivanov", "age2": 30},
                },
            ],
        )