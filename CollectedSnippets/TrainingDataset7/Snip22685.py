def test_typedchoicefield_3(self):
        # This can also cause weirdness: be careful (bool(-1) == True,
        # remember)
        f = TypedChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=bool)
        self.assertTrue(f.clean("-1"))