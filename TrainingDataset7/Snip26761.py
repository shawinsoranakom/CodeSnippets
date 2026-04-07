async def test_process_template_response(self):
        response = await self.async_client.get(
            "/middleware_exceptions/template_response/"
        )
        self.assertEqual(
            response.content,
            b"template_response OK\nAsyncTemplateResponseMiddleware",
        )