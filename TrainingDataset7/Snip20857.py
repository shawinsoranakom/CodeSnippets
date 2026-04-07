async def test_condition_decorator_async_view(self):
        @condition(
            etag_func=self.etag_func,
            last_modified_func=self.latest_entry,
        )
        async def async_view(request):
            return HttpResponse()

        request = HttpRequest()
        request.method = "GET"
        response = await async_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["ETag"], '"b4246ffc4f62314ca13147c9d4f76974"')
        self.assertEqual(
            response.headers["Last-Modified"],
            "Mon, 02 Jan 2023 23:21:47 GMT",
        )