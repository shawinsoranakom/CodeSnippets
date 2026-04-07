def test_empty(self):
        obj = Author.objects.annotate(json_array=JSONArray()).first()
        self.assertEqual(obj.json_array, [])