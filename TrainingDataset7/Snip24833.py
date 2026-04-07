def test_json_response_uuid(self):
        u = uuid.uuid4()
        response = JsonResponse(u, safe=False)
        self.assertEqual(json.loads(response.text), str(u))