def test_prefix_braces(self):
        self.assertEqual(
            "/%7B%7Binvalid%7D%7D/includes/non_path_include/",
            reverse("non_path_include"),
        )