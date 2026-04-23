def test_exception_in_middleware_converted_before_prior_middleware(self):
        response = self.client.get("/middleware_exceptions/view/")
        self.assertEqual(mw.log, [(404, response.content)])
        self.assertEqual(response.status_code, 404)