def test_login_required_paths(self):
        paths = ["login_required_cbv_view", "login_required_decorator_view"]
        for path in paths:
            response = self.client.get(f"/{path}/")
            self.assertRedirects(
                response,
                "/custom_login/" + f"?step=/{path}/",
                fetch_redirect_response=False,
            )