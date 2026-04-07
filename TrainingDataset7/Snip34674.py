async def test_query_params(self):
        tests = (
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "trace",
        )
        for method in tests:
            with self.subTest(method=method):
                client_method = getattr(self.async_client, method)
                response = await client_method(
                    "/async_get_view/", query_params={"example": "data"}
                )
                self.assertEqual(response.asgi_request.GET["example"], "data")