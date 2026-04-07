def test_shuffle_key(self):
        cases = [
            (lambda x: x, ["a", "d", "b", "c"]),
            (lambda x: x.upper(), ["d", "c", "a", "b"]),
        ]
        for num, (key, expected) in enumerate(cases, start=1):
            with self.subTest(num=num):
                shuffler = Shuffler(seed=1234)
                actual = shuffler.shuffle(["a", "b", "c", "d"], key)
                self.assertEqual(actual, expected)