def test_expressions(self):
        obj = Author.objects.annotate(
            json_array=JSONArray(
                Lower("name"),
                F("alias"),
                F("goes_by"),
                Value(30000.15),
                F("age") * 2,
            )
        ).first()
        self.assertEqual(
            obj.json_array,
            [
                "ivan ivanov",
                "iivanov",
                None,
                30000.15,
                60,
            ],
        )