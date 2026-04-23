def test_pickling_cookie(self):
        response = SimpleTemplateResponse(
            "first/test.html",
            {
                "value": 123,
                "fn": datetime.now,
            },
        )

        response.cookies["key"] = "value"

        response.render()
        pickled_response = pickle.dumps(response, pickle.HIGHEST_PROTOCOL)
        unpickled_response = pickle.loads(pickled_response)

        self.assertEqual(unpickled_response.cookies["key"].value, "value")