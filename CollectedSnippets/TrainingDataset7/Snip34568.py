async def test_copy_response_async(self):
        response = await self.async_client.get("/async_get_view/")
        response_copy = copy.copy(response)
        self.assertEqual(repr(response), repr(response_copy))
        self.assertIs(response_copy.client, response.client)
        self.assertIs(response_copy.resolver_match, response.resolver_match)
        self.assertIs(response_copy.asgi_request, response.asgi_request)