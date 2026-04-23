def test_missing_response_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            log_response("No response provided", response=None, request=self.request)