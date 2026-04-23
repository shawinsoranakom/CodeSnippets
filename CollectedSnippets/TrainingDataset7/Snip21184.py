def test_allows_reordering_keyword_only_params(self):
        """Keyword-only params can be freely added and rearranged."""

        # Original signature: some_func(b=2, a=1), and remappable_names
        # reflects the original positional argument order.
        @deprecate_posargs(RemovedAfterNextVersionWarning, ["b", "a"])
        def some_func(*, aa_new=0, a=1, b=2):
            return aa_new, a, b

        with self.assertDeprecated("'b', 'a'", "some_func"):
            result = some_func(20, 10)
        self.assertEqual(result, (0, 10, 20))