def test_prefix_format_char(self):
        self.assertEqual(
            "/bump%2520map/includes/non_path_include/", reverse("non_path_include")
        )