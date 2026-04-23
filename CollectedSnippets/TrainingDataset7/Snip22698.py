def test_typedmultiplechoicefield_7(self):
        # If you want cleaning an empty value to return a different type, tell
        # the field
        f = TypedMultipleChoiceField(
            choices=[(1, "+1"), (-1, "-1")],
            coerce=int,
            required=False,
            empty_value=None,
        )
        self.assertIsNone(f.clean([]))