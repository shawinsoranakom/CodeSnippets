def test_paths_with_logged_in_user(self):
        paths = [
            "public_view",
            "public_function_view",
            "protected_view",
            "protected_function_view",
            "login_required_cbv_view",
            "login_required_decorator_view",
        ]
        self.client.login(username="test_user", password="test_password")
        for path in paths:
            response = self.client.get(f"/{path}/")
            self.assertEqual(response.status_code, 200)