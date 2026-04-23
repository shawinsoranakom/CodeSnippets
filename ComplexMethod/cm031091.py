def test_walk_many_open_files(self):
        depth = 30
        base = os.path.join(os_helper.TESTFN, 'deep')
        p = os.path.join(base, *(['d']*depth))
        os.makedirs(p)

        iters = [self.walk(base, topdown=False) for j in range(100)]
        for i in range(depth + 1):
            expected = (p, ['d'] if i else [], [])
            for it in iters:
                self.assertEqual(next(it), expected)
            p = os.path.dirname(p)

        iters = [self.walk(base, topdown=True) for j in range(100)]
        p = base
        for i in range(depth + 1):
            expected = (p, ['d'] if i < depth else [], [])
            for it in iters:
                self.assertEqual(next(it), expected)
            p = os.path.join(p, 'd')