def test_login_url_resolve_logic(self):
        paths = ["login_required_cbv_view", "login_required_decorator_view"]
        for path in paths:
            response = self.client.get(f"/{path}/")
            self.assertRedirects(
                response,
                "/custom_login/" + f"?step=/{path}/",
                fetch_redirect_response=False,
            )
        paths = ["protected_view", "protected_function_view"]
        for path in paths:
            response = self.client.get(f"/{path}/")
            self.assertRedirects(
                response,
                f"/settings_login/?redirect_to=/{path}/",
                fetch_redirect_response=False,
            )