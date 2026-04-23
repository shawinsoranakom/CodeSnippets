def test_empty(self):
        obj = Author.objects.annotate(json_object=JSONObject()).first()
        self.assertEqual(obj.json_object, {})