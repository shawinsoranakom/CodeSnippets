def _choose_a2(self, i1):
        """
        Choose the second alpha using a heuristic algorithm
        Steps:
            1: Choose alpha2 that maximizes the step size (|E1 - E2|).
            2: Start in a random point, loop over all non-bound samples till alpha1 and
               alpha2 are optimized.
            3: Start in a random point, loop over all samples till alpha1 and alpha2 are
               optimized.
        """
        self._unbound = [i for i in self._all_samples if self._is_unbound(i)]

        if len(self.unbound) > 0:
            tmp_error = self._error.copy().tolist()
            tmp_error_dict = {
                index: value
                for index, value in enumerate(tmp_error)
                if self._is_unbound(index)
            }
            if self._e(i1) >= 0:
                i2 = min(tmp_error_dict, key=lambda index: tmp_error_dict[index])
            else:
                i2 = max(tmp_error_dict, key=lambda index: tmp_error_dict[index])
            cmd = yield i1, i2
            if cmd is None:
                return

        rng = np.random.default_rng()
        for i2 in np.roll(self.unbound, rng.choice(self.length)):
            cmd = yield i1, i2
            if cmd is None:
                return

        for i2 in np.roll(self._all_samples, rng.choice(self.length)):
            cmd = yield i1, i2
            if cmd is None:
                return