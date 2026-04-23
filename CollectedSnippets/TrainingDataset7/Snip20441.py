def test_nested_empty_json_array(self):
        obj = Author.objects.annotate(
            json_array=JSONArray(
                F("name"),
                JSONArray(),
            )
        ).first()
        self.assertEqual(
            obj.json_array,
            [
                "Ivan Ivanov",
                [],
            ],
        )