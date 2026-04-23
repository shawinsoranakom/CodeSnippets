def test_find_many_lengths(self):
        haystack_repeats = [a * 10**e for e in range(6) for a in (1,2,5)]
        haystacks = [(n, self.fixtype("abcab"*n + "da")) for n in haystack_repeats]

        needle_repeats = [a * 10**e for e in range(6) for a in (1, 3)]
        needles = [(m, self.fixtype("abcab"*m + "da")) for m in needle_repeats]

        for n, haystack1 in haystacks:
            haystack2 = haystack1[:-1]
            for m, needle in needles:
                answer1 = 5 * (n - m) if m <= n else -1
                self.assertEqual(haystack1.find(needle), answer1, msg=(n,m))
                self.assertEqual(haystack2.find(needle), -1, msg=(n,m))