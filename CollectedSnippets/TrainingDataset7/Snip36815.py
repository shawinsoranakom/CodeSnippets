def test_wrong_url_value_raises_error(self):
        mtv = ModelToValidate(number=10, name="Some Name", url="not a url")
        self.assertFieldFailsValidationWithMessage(
            mtv.full_clean, "url", ["Enter a valid URL."]
        )