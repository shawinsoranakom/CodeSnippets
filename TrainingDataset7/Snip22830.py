def test_empty_permitted_and_use_required_attribute(self):
        msg = (
            "The empty_permitted and use_required_attribute arguments may not "
            "both be True."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Person(empty_permitted=True, use_required_attribute=True)