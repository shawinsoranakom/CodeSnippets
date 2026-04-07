def test_basic(self):
        obj = Author.objects.annotate(json_object=JSONObject(name="name")).first()
        self.assertEqual(obj.json_object, {"name": "Ivan Ivanov"})