def test_typedchoicefield_1(self):
        f = TypedChoiceField(choices=[(1, "+1"), (-1, "-1")], coerce=int)
        self.assertEqual(1, f.clean("1"))
        msg = "'Select a valid choice. 2 is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("2")