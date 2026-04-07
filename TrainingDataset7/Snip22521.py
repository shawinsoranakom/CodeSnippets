def test_datefield_5(self):
        # Test null bytes (#18982)
        f = DateField()
        with self.assertRaisesMessage(ValidationError, "'Enter a valid date.'"):
            f.clean("a\x00b")