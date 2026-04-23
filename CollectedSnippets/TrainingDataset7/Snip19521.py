def test_simple_call(self):
        call_command("check")
        self.assertEqual(
            simple_system_check.kwargs,
            {"app_configs": None, "databases": ["default", "other"]},
        )
        self.assertEqual(
            tagged_system_check.kwargs,
            {"app_configs": None, "databases": ["default", "other"]},
        )