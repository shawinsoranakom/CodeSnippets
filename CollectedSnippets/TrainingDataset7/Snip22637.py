def test_validate_duplicated_values(self):
        f = MultipleChoiceField(
            choices=[
                ("1", "One"),
                ("2", "Two"),
                ("3", "Three"),
                ("4", "Four"),
                ("5", "Five"),
            ]
        )
        self.assertIsNone(f.validate(["4", "4", "5", "5"]))