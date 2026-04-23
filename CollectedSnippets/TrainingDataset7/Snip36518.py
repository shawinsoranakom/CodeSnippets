def test_len(self):
        for seq in ["asd", [1, 2, 3], {"a": 1, "b": 2, "c": 3}]:
            obj = self.lazy_wrap(seq)
            self.assertEqual(len(obj), 3)