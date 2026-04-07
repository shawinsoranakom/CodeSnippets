def test_bad_class_based_handlers(self):
        result = check_custom_error_handlers(None)
        self.assertEqual(len(result), 4)
        for code, num_params, error in zip([400, 403, 404, 500], [2, 2, 2, 1], result):
            with self.subTest("handler%s" % code):
                self.assertEqual(
                    error,
                    Error(
                        "The custom handler%s view 'check_framework.urls."
                        "bad_class_based_error_handlers.HandlerView.as_view."
                        "<locals>.view' does not take the correct number of "
                        "arguments (request%s)."
                        % (
                            code,
                            ", exception" if num_params == 2 else "",
                        ),
                        id="urls.E007",
                    ),
                )