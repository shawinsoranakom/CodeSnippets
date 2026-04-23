def test_symmetric_difference(self):
        population = (-4, -3, -2, -1, 0, 1, 2, 3, 4)

        for a, b1, b2, c in product(population, repeat=4):
            p = Counter(a=a, b=b1)
            q = Counter(b=b2, c=c)
            r = p ^ q

            # Elementwise invariants
            for k in ('a', 'b', 'c'):
                self.assertEqual(r[k], max(p[k], q[k]) - min(p[k], q[k]))
                self.assertEqual(r[k], abs(p[k] - q[k]))

            # Invariant for all positive, negative, and zero counts
            self.assertEqual(r, (p - q) | (q - p))

            # Invariant for non-negative counts
            if a >= 0 and b1 >= 0 and b2 >= 0 and c >= 0:
                self.assertEqual(r, (p | q) - (p & q))

            # Zeros and negatives eliminated
            self.assertTrue(all(value > 0 for value in r.values()))

            # Output preserves input order:  p first and then q
            keys = list(p) + list(q)
            indices = [keys.index(k) for k in r]
            self.assertEqual(indices, sorted(indices))

            # Inplace operation matches binary operation
            pp = Counter(p)
            qq = Counter(q)
            pp ^= qq
            self.assertEqual(pp, r)