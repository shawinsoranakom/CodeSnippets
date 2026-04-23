def test_json_response_list(self):
        response = JsonResponse(["foo", "bar"], safe=False)
        self.assertEqual(json.loads(response.text), ["foo", "bar"])