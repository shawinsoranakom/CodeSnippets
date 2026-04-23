def test_typedchoicefield_special_coerce(self):
        """
        A coerce function which results in a value not present in choices
        should raise an appropriate error (#21397).
        """

        def coerce_func(val):
            return decimal.Decimal("1.%s" % val)

        f = TypedChoiceField(
            choices=[(1, "1"), (2, "2")], coerce=coerce_func, required=True
        )
        self.assertEqual(decimal.Decimal("1.2"), f.clean("2"))
        with self.assertRaisesMessage(ValidationError, "'This field is required.'"):
            f.clean("")
        msg = "'Select a valid choice. 3 is not one of the available choices.'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("3")