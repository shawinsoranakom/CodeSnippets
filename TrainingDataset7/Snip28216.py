def test_invalid_choice(self):
        model_instance = None  # Actual model instance not needed.
        self.no_choices.validate(0, model_instance)
        msg = "['Value 99 is not a valid choice.']"
        with self.assertRaisesMessage(ValidationError, msg):
            self.empty_choices.validate(99, model_instance)
        with self.assertRaisesMessage(ValidationError, msg):
            self.with_choices.validate(99, model_instance)