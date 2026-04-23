def test_index(self):
        for n in 1, 2, 30, 40, 200:

            d = deque(range(n))
            for i in range(n):
                self.assertEqual(d.index(i), i)

            with self.assertRaises(ValueError):
                d.index(n+1)

            # Test detection of mutation during iteration
            d = deque(range(n))
            d[n//2] = MutateCmp(d, False)
            with self.assertRaises(RuntimeError):
                d.index(n)

            # Test detection of comparison exceptions
            d = deque(range(n))
            d[n//2] = BadCmp()
            with self.assertRaises(RuntimeError):
                d.index(n)

        # Test start and stop arguments behavior matches list.index()
        elements = 'ABCDEFGHI'
        nonelement = 'Z'
        d = deque(elements * 2)
        s = list(elements * 2)
        for start in range(-5 - len(s)*2, 5 + len(s) * 2):
            for stop in range(-5 - len(s)*2, 5 + len(s) * 2):
                for element in elements + 'Z':
                    try:
                        target = s.index(element, start, stop)
                    except ValueError:
                        with self.assertRaises(ValueError):
                            d.index(element, start, stop)
                    else:
                        self.assertEqual(d.index(element, start, stop), target)

        # Test large start argument
        d = deque(range(0, 10000, 10))
        for step in range(100):
            i = d.index(8500, 700)
            self.assertEqual(d[i], 8500)
            # Repeat test with a different internal offset
            d.rotate()