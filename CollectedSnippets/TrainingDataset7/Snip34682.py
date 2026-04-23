def test_cannot_use_data_and_query_params_together(self):
        tests = ["get", "head"]
        msg = "query_params and data arguments are mutually exclusive."
        for method in tests:
            with self.subTest(method=method):
                factory = getattr(self.request_factory, method)
                with self.assertRaisesMessage(ValueError, msg):
                    factory(
                        "/somewhere",
                        data={"example": "data"},
                        query_params={"q": "terms"},
                    )