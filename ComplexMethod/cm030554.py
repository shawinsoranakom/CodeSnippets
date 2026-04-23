def test_equal_sized_groups(self):
        quantiles = statistics.quantiles
        total = 10_000
        data = [random.expovariate(0.2) for i in range(total)]
        while len(set(data)) != total:
            data.append(random.expovariate(0.2))
        data.sort()

        # Cases where the group size exactly divides the total
        for n in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
            group_size = total // n
            self.assertEqual(
                [bisect.bisect(data, q) for q in quantiles(data, n=n)],
                list(range(group_size, total, group_size)))

        # When the group sizes can't be exactly equal, they should
        # differ by no more than one
        for n in (13, 19, 59, 109, 211, 571, 1019, 1907, 5261, 9769):
            group_sizes = {total // n, total // n + 1}
            pos = [bisect.bisect(data, q) for q in quantiles(data, n=n)]
            sizes = {q - p for p, q in zip(pos, pos[1:])}
            self.assertTrue(sizes <= group_sizes)