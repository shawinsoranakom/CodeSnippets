def test_applied_to_lambda(self):
        """
        Please don't try to deprecate lambda args! What does that even mean?!
        (But if it happens, the decorator should do something reasonable.)
        """
        lambda_func = deprecate_posargs(RemovedAfterNextVersionWarning, ["b"])(
            lambda a, *, b=1: (a, b)
        )
        with self.assertDeprecated("'b'", "<lambda>"):
            result = lambda_func(10, 20)
        self.assertEqual(result, (10, 20))