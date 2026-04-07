def test_decorator_requires_mapping(self):
        for config, decorator in product(
            [None, 0, False, [], [1, 2, 3], 42, {4, 5}],
            (csp_override, csp_report_only_override),
        ):
            with (
                self.subTest(config=config, decorator=decorator),
                self.assertRaisesMessage(TypeError, "CSP config should be a mapping"),
            ):
                decorator(config)