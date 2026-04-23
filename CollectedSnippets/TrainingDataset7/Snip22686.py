def test_typedchoicefield_4(self):
        # Even more weirdness: if you have a valid choice but your coercion
        # function can't coerce, you'll still get a validation error. Don't do
        # this!
        f = TypedChoiceField(choices=[("A", "A"), ("B", "B")], coerce=int)
        msg = "'Select a valid choice. B is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("B")
        # Required fields require values
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")