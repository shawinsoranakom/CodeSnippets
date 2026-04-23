def test_json_response_text(self):
        response = JsonResponse("foobar", safe=False)
        self.assertEqual(json.loads(response.text), "foobar")