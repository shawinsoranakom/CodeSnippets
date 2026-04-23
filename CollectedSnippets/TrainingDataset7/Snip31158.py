def test_non_view_callable_raises_no_reverse_match(self):
        """
        Passing a non-view callable into resolve_url() raises a
        NoReverseMatch exception.
        """
        with self.assertRaises(NoReverseMatch):
            resolve_url(lambda: "asdf")