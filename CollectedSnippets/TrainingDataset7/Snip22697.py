def test_typedmultiplechoicefield_6(self):
        # Non-required fields aren't required
        f = TypedMultipleChoiceField(
            choices=[(1, "+1"), (-1, "-1")], coerce=int, required=False
        )
        self.assertEqual([], f.clean([]))