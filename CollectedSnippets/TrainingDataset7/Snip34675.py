async def test_request_factory(self):
        tests = (
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "trace",
        )
        for method_name in tests:
            with self.subTest(method=method_name):

                async def async_generic_view(request):
                    if request.method.lower() != method_name:
                        return HttpResponseNotAllowed(method_name)
                    return HttpResponse(status=200)

                method = getattr(self.request_factory, method_name)
                request = method("/somewhere/")
                response = await async_generic_view(request)
                self.assertEqual(response.status_code, 200)