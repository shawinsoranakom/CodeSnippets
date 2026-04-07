async def test_exception_in_async_render_passed_to_process_exception(self):
        response = await self.async_client.get(
            "/middleware_exceptions/async_exception_in_render/"
        )
        self.assertEqual(response.content, b"Exception caught")