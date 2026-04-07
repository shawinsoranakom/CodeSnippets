def test_custom_null_message(self):
        cmm = CustomMessagesModel()
        self.assertFieldFailsValidationWithMessage(cmm.full_clean, "number", ["NULL"])