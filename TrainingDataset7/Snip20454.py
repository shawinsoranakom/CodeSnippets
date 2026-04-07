def test_expressions(self):
        obj = Author.objects.annotate(
            json_object=JSONObject(
                name=Lower("name"),
                alias="alias",
                goes_by="goes_by",
                salary=Value(30000.15),
                age=F("age") * 2,
            )
        ).first()
        self.assertEqual(
            obj.json_object,
            {
                "name": "ivan ivanov",
                "alias": "iivanov",
                "goes_by": None,
                "salary": 30000.15,
                "age": 60,
            },
        )