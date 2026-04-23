async def test_process_view_return_response(self):
        response = await self.async_client.get("/middleware_exceptions/view/")
        self.assertEqual(response.content, b"Processed view normal_view")