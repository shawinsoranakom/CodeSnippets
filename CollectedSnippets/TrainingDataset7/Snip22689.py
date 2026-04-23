def test_typedchoicefield_has_changed(self):
        # has_changed should not trigger required validation
        f = TypedChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=int, required=True)
        self.assertFalse(f.has_changed(None, ""))
        self.assertFalse(f.has_changed(1, "1"))
        self.assertFalse(f.has_changed("1", "1"))

        f = TypedChoiceField(
            choices=[("", "---------"), ("a", "a"), ("b", "b")],
            coerce=str,
            required=False,
            initial=None,
            empty_value=None,
        )
        self.assertFalse(f.has_changed(None, ""))
        self.assertTrue(f.has_changed("", "a"))
        self.assertFalse(f.has_changed("a", "a"))