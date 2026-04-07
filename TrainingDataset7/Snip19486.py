def test_bad_function_based_handlers(self):
        result = check_custom_error_handlers(None)
        self.assertEqual(len(result), 4)
        for code, num_params, error in zip([400, 403, 404, 500], [2, 2, 2, 1], result):
            with self.subTest("handler{}".format(code)):
                self.assertEqual(
                    error,
                    Error(
                        "The custom handler{} view 'check_framework.urls."
                        "bad_function_based_error_handlers.bad_handler' "
                        "does not take the correct number of arguments "
                        "(request{}).".format(
                            code, ", exception" if num_params == 2 else ""
                        ),
                        id="urls.E007",
                    ),
                )