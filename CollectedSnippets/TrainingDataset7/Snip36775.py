def test_custom_simple_validator_message(self):
        cmm = CustomMessagesModel(number=12)
        self.assertFieldFailsValidationWithMessage(cmm.full_clean, "number", ["AAARGH"])