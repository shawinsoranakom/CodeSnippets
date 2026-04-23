def test_typeCasts(self):
        for k, v in TEST_CASES.items():
            for inpt, expected in v:
                with self.subTest(k=k, inpt=inpt):
                    got = getattr(typecasts, k)(inpt)
                    self.assertEqual(
                        got,
                        expected,
                        "In %s: %r doesn't match %r. Got %r instead."
                        % (k, inpt, expected, got),
                    )