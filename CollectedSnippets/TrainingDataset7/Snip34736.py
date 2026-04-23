def test_basic_contains_not_contains(self):
        response = self.client.get("/no_template_view/")

        with self.subTest("assertNotContains"):
            self.assertNotContains(response, "never")

        cases = [
            ("never", 0),
            ("once", None),
            ("once", 1),
            ("twice", None),
            ("twice", 2),
        ]

        for text, expected_count in cases:
            with self.subTest(text=text, expected_count=expected_count):
                if expected_count is not None:
                    self.assertContains(response, text, count=expected_count)
                else:
                    self.assertContains(response, text)