def test_unique_together(self):
        grand_child = GrandChild(
            email="grand_child@example.com",
            first_name=self.grand_parent.first_name,
            last_name=self.grand_parent.last_name,
        )
        msg = "Grand parent with this First name and Last name already exists."
        with self.assertRaisesMessage(ValidationError, msg):
            grand_child.validate_unique()