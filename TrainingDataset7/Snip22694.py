def test_typedmultiplechoicefield_3(self):
        # This can also cause weirdness: be careful (bool(-1) == True,
        # remember)
        f = TypedMultipleChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=bool)
        self.assertEqual([True], f.clean(["-1"]))