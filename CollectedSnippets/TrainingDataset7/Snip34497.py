def test_repickling(self):
        response = SimpleTemplateResponse(
            "first/test.html",
            {
                "value": 123,
                "fn": datetime.now,
            },
        )
        with self.assertRaises(ContentNotRenderedError):
            pickle.dumps(response)

        response.render()
        pickled_response = pickle.dumps(response)
        unpickled_response = pickle.loads(pickled_response)
        pickle.dumps(unpickled_response)