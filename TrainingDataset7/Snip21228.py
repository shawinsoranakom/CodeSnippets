def test_repr(self):
        class GetResponse:
            def __call__(self):
                return HttpResponse()

        def get_response():
            return HttpResponse()

        self.assertEqual(
            repr(MiddlewareMixin(GetResponse())),
            "<MiddlewareMixin get_response=GetResponse>",
        )
        self.assertEqual(
            repr(MiddlewareMixin(get_response)),
            "<MiddlewareMixin get_response="
            "MiddlewareMixinTests.test_repr.<locals>.get_response>",
        )
        self.assertEqual(
            repr(CsrfViewMiddleware(GetResponse())),
            "<CsrfViewMiddleware get_response=GetResponse>",
        )
        self.assertEqual(
            repr(CsrfViewMiddleware(get_response)),
            "<CsrfViewMiddleware get_response="
            "MiddlewareMixinTests.test_repr.<locals>.get_response>",
        )