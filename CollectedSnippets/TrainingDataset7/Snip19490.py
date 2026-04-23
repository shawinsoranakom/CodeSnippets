def test_good_function_based_handlers_deferred_annotations(self):
        result = check_custom_error_handlers(None)
        self.assertEqual(result, [])