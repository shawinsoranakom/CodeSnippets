def test_in_and_not_in(self):
        for sc5 in IteratingSequenceClass(5), SequenceClass(5):
            for i in range(5):
                self.assertIn(i, sc5)
            for i in "abc", -1, 5, 42.42, (3, 4), [], {1: 1}, 3-12j, sc5:
                self.assertNotIn(i, sc5)

        self.assertIn(ALWAYS_EQ, IteratorProxyClass(iter([1])))
        self.assertIn(ALWAYS_EQ, SequenceProxyClass([1]))
        self.assertNotIn(ALWAYS_EQ, IteratorProxyClass(iter([NEVER_EQ])))
        self.assertNotIn(ALWAYS_EQ, SequenceProxyClass([NEVER_EQ]))
        self.assertIn(NEVER_EQ, IteratorProxyClass(iter([ALWAYS_EQ])))
        self.assertIn(NEVER_EQ, SequenceProxyClass([ALWAYS_EQ]))

        self.assertRaises(TypeError, lambda: 3 in 12)
        self.assertRaises(TypeError, lambda: 3 not in map)
        self.assertRaises(ZeroDivisionError, lambda: 3 in BadIterableClass())

        d = {"one": 1, "two": 2, "three": 3, 1j: 2j}
        for k in d:
            self.assertIn(k, d)
            self.assertNotIn(k, d.values())
        for v in d.values():
            self.assertIn(v, d.values())
            self.assertNotIn(v, d)
        for k, v in d.items():
            self.assertIn((k, v), d.items())
            self.assertNotIn((v, k), d.items())

        f = open(TESTFN, "w", encoding="utf-8")
        try:
            f.write("a\n" "b\n" "c\n")
        finally:
            f.close()
        f = open(TESTFN, "r", encoding="utf-8")
        try:
            for chunk in "abc":
                f.seek(0, 0)
                self.assertNotIn(chunk, f)
                f.seek(0, 0)
                self.assertIn((chunk + "\n"), f)
        finally:
            f.close()
            try:
                unlink(TESTFN)
            except OSError:
                pass