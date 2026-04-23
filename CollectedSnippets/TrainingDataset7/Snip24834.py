def test_json_response_custom_encoder(self):
        class CustomDjangoJSONEncoder(DjangoJSONEncoder):
            def encode(self, o):
                return json.dumps({"foo": "bar"})

        response = JsonResponse({}, encoder=CustomDjangoJSONEncoder)
        self.assertEqual(json.loads(response.text), {"foo": "bar"})