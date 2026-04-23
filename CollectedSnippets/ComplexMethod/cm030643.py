def multipass(cls, barrier, results, n):
        m = barrier.parties
        assert m == cls.N
        for i in range(n):
            results[0].append(True)
            assert len(results[1]) == i * m
            barrier.wait()
            results[1].append(True)
            assert len(results[0]) == (i + 1) * m
            barrier.wait()
        try:
            assert barrier.n_waiting == 0
        except NotImplementedError:
            pass
        assert not barrier.broken