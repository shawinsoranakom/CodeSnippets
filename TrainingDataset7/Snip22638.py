def test_validate_duplicated_invalid_values(self):
        f = MultipleChoiceField(choices=[("1", "one"), ("2", "Two")])
        with self.assertRaisesMessage(ValidationError, "invalid-one"):
            f.validate(["invalid-one", "invalid-one", "invalid-two"])