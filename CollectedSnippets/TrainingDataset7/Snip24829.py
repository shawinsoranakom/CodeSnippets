def test_json_response_non_ascii(self):
        data = {"key": "łóżko"}
        response = JsonResponse(data)
        self.assertEqual(json.loads(response.text), data)