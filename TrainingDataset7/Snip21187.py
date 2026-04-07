def test_avoids_remapping_to_new_keyword_arguments(self):
        # Only 'b' is moving; 'c' was added later.
        @deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])
        def func(a, *, b=1, c=2):
            return a, b, c

        with self.assertRaisesMessage(
            TypeError,
            "func() takes at most 2 positional argument(s) (including 1 deprecated) "
            "but 3 were given.",
        ):
            func(10, 20, 30)