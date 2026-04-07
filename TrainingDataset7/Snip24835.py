def test_json_response_passing_arguments_to_json_dumps(self):
        response = JsonResponse({"foo": "bar"}, json_dumps_params={"indent": 2})
        self.assertEqual(response.text, '{\n  "foo": "bar"\n}')