def test_typedchoicefield_6(self):
        f = TypedChoiceField(
            choices=[(1, "+1"), (-1, "-1")],
            coerce=int,
            required=False,
            empty_value=None,
        )
        self.assertIsNone(f.clean(""))