def test_prefix_parenthesis(self):
        # Parentheses are allowed and should not cause errors or be escaped
        with override_script_prefix("/bogus)/"):
            self.assertEqual(
                "/bogus)/includes/non_path_include/", reverse("non_path_include")
            )
        with override_script_prefix("/(bogus)/"):
            self.assertEqual(
                "/(bogus)/includes/non_path_include/", reverse("non_path_include")
            )