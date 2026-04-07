def test_given_app(self):
        call_command("check", "auth", "admin")
        auth_config = apps.get_app_config("auth")
        admin_config = apps.get_app_config("admin")
        self.assertEqual(
            simple_system_check.kwargs,
            {
                "app_configs": [auth_config, admin_config],
                "databases": ["default", "other"],
            },
        )
        self.assertEqual(
            tagged_system_check.kwargs,
            {
                "app_configs": [auth_config, admin_config],
                "databases": ["default", "other"],
            },
        )