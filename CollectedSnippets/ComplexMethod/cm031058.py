def test_walk_many_open_files(self):
        depth = 30
        base = self.cls(self.base, 'deep')
        path = self.cls(base, *(['d']*depth))
        path.mkdir(parents=True)

        iters = [base.walk(top_down=False) for _ in range(100)]
        for i in range(depth + 1):
            expected = (path, ['d'] if i else [], [])
            for it in iters:
                self.assertEqual(next(it), expected)
            path = path.parent

        iters = [base.walk(top_down=True) for _ in range(100)]
        path = base
        for i in range(depth + 1):
            expected = (path, ['d'] if i < depth else [], [])
            for it in iters:
                self.assertEqual(next(it), expected)
            path = path / 'd'