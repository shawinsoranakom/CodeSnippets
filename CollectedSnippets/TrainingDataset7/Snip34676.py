async def test_request_factory_data(self):
        async def async_generic_view(request):
            return HttpResponse(status=200, content=request.body)

        request = self.request_factory.post(
            "/somewhere/",
            data={"example": "data"},
            content_type="application/json",
        )
        self.assertEqual(request.headers["content-length"], "19")
        self.assertEqual(request.headers["content-type"], "application/json")
        response = await async_generic_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"example": "data"}')