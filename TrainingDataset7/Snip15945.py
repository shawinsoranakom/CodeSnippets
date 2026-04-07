def test_cyclic(self):
        self._connect(0, 2)
        self._connect(1, 0)
        self._connect(2, 1)
        self._collect(0)
        self._check([0, [1, [2]]])