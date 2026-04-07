def test_given_tag(self):
        call_command("check", tags=["simpletag"])
        self.assertIsNone(simple_system_check.kwargs)
        self.assertEqual(
            tagged_system_check.kwargs,
            {"app_configs": None, "databases": ["default", "other"]},
        )