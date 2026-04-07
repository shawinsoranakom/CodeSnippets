def test_shuffle_consistency(self):
        seq = [str(n) for n in range(5)]
        cases = [
            (None, ["3", "0", "2", "4", "1"]),
            (0, ["3", "2", "4", "1"]),
            (1, ["3", "0", "2", "4"]),
            (2, ["3", "0", "4", "1"]),
            (3, ["0", "2", "4", "1"]),
            (4, ["3", "0", "2", "1"]),
        ]
        shuffler = Shuffler(seed=1234)
        for index, expected in cases:
            with self.subTest(index=index):
                if index is None:
                    new_seq = seq
                else:
                    new_seq = seq.copy()
                    del new_seq[index]
                actual = shuffler.shuffle(new_seq, lambda x: x)
                self.assertEqual(actual, expected)