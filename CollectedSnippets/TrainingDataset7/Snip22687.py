def test_typedchoicefield_5(self):
        # Non-required fields aren't required
        f = TypedChoiceField(
            choices=[(1, "+1"), (-1, "-1")], coerce=int, required=False
        )
        self.assertEqual("", f.clean(""))