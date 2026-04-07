def test_typedmultiplechoicefield_has_changed(self):
        # has_changed should not trigger required validation
        f = TypedMultipleChoiceField(
            choices=[(1, "+1"), (-1, "-1")], coerce=int, required=True
        )
        self.assertFalse(f.has_changed(None, ""))