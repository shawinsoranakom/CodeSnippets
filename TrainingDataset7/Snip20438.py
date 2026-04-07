def test_basic(self):
        obj = Author.objects.annotate(
            json_array=JSONArray(Value("name"), F("name"))
        ).first()
        self.assertEqual(obj.json_array, ["name", "Ivan Ivanov"])