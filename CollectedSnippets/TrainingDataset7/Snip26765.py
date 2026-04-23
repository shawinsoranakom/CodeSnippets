async def test_view_exception_handled_by_process_exception(self):
        response = await self.async_client.get("/middleware_exceptions/error/")
        self.assertEqual(response.content, b"Exception caught")