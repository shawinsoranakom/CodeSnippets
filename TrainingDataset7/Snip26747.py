def test_raise_exception(self):
        request = self.rf.get("middleware_exceptions/view/")
        with self.assertRaises(MiddlewareNotUsed):
            MyMiddleware(lambda req: HttpResponse()).process_request(request)