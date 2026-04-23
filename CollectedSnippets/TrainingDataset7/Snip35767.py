def test_reverse_none(self):
        # Reversing None should raise an error, not return the last un-named
        # view.
        with self.assertRaises(NoReverseMatch):
            reverse(None)