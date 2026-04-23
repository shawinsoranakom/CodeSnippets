def test_protected_paths(self):
        paths = ["protected_view", "protected_function_view"]
        for path in paths:
            response = self.client.get(f"/{path}/")
            self.assertRedirects(
                response,
                settings.LOGIN_URL + f"?next=/{path}/",
                fetch_redirect_response=False,
            )