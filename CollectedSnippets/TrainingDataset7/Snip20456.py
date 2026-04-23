def test_nested_empty_json_object(self):
        obj = Author.objects.annotate(
            json_object=JSONObject(
                name="name",
                nested_json_object=JSONObject(),
            )
        ).first()
        self.assertEqual(
            obj.json_object,
            {
                "name": "Ivan Ivanov",
                "nested_json_object": {},
            },
        )