def test_nested_json_array(self):
        obj = Author.objects.annotate(
            json_array=JSONArray(
                F("name"),
                JSONArray(F("alias"), F("age")),
            )
        ).first()
        self.assertEqual(
            obj.json_array,
            [
                "Ivan Ivanov",
                ["iivanov", 30],
            ],
        )