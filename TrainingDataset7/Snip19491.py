def test_good_class_based_handlers(self):
        result = check_custom_error_handlers(None)
        self.assertEqual(result, [])