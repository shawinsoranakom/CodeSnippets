def test_unique(self):
        grand_child = GrandChild(
            email=self.grand_parent.email,
            first_name="grand",
            last_name="child",
        )
        msg = "Grand parent with this Email already exists."
        with self.assertRaisesMessage(ValidationError, msg):
            grand_child.validate_unique()