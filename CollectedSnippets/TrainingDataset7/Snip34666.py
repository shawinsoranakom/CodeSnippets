async def test_response_resolver_match(self):
        response = await self.async_client.get("/async_get_view/")
        self.assertTrue(hasattr(response, "resolver_match"))
        self.assertEqual(response.resolver_match.url_name, "async_get_view")