async def test_follow_redirect(self):
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
        for method_name in tests:
            with self.subTest(method=method_name):
                method = getattr(self.async_client, method_name)
                response = await method("/redirect_view/", follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.resolver_match.url_name, "get_view")