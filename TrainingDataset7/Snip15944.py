def test_non_added_parent(self):
        self._connect(0, 1)
        self._collect(0)
        self._check([0])