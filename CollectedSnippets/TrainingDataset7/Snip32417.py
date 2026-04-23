async def test_get_async_response(self):
        request = self.async_request_factory.get("/static/test/file.txt")
        handler = ASGIStaticFilesHandler(ASGIHandler())
        response = await handler.get_response_async(request)
        response.close()
        self.assertEqual(response.status_code, 200)