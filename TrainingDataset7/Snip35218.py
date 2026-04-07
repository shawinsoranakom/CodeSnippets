def test_undefined_order(self):
        # Using an unordered queryset with more than one ordered value
        # is an error.
        msg = (
            "Trying to compare non-ordered queryset against more than one "
            "ordered value."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.assertQuerySetEqual(
                Person.objects.all(),
                [self.p1, self.p2],
            )
        # No error for one value.
        self.assertQuerySetEqual(Person.objects.filter(name="p1"), [self.p1])