async def test_get_async_response_not_found(self):
        request = self.async_request_factory.get("/static/test/not-found.txt")
        handler = ASGIStaticFilesHandler(ASGIHandler())
        response = await handler.get_response_async(request)
        self.assertEqual(response.status_code, 404)