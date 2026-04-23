def fit(self):
        k = self._k
        state = None
        while True:
            # 1: Find alpha1, alpha2
            try:
                i1, i2 = self.choose_alpha.send(state)
                state = None
            except StopIteration:
                print("Optimization done!\nEvery sample satisfy the KKT condition!")
                break

            # 2: calculate new alpha2 and new alpha1
            y1, y2 = self.tags[i1], self.tags[i2]
            a1, a2 = self.alphas[i1].copy(), self.alphas[i2].copy()
            e1, e2 = self._e(i1), self._e(i2)
            args = (i1, i2, a1, a2, e1, e2, y1, y2)
            a1_new, a2_new = self._get_new_alpha(*args)
            if not a1_new and not a2_new:
                state = False
                continue
            self.alphas[i1], self.alphas[i2] = a1_new, a2_new

            # 3: update threshold(b)
            b1_new = np.float64(
                -e1
                - y1 * k(i1, i1) * (a1_new - a1)
                - y2 * k(i2, i1) * (a2_new - a2)
                + self._b
            )
            b2_new = np.float64(
                -e2
                - y2 * k(i2, i2) * (a2_new - a2)
                - y1 * k(i1, i2) * (a1_new - a1)
                + self._b
            )
            if 0.0 < a1_new < self._c:
                b = b1_new
            if 0.0 < a2_new < self._c:
                b = b2_new
            if not (np.float64(0) < a2_new < self._c) and not (
                np.float64(0) < a1_new < self._c
            ):
                b = (b1_new + b2_new) / 2.0
            b_old = self._b
            self._b = b

            # 4: update error, here we only calculate the error for non-bound samples
            self._unbound = [i for i in self._all_samples if self._is_unbound(i)]
            for s in self.unbound:
                if s in (i1, i2):
                    continue
                self._error[s] += (
                    y1 * (a1_new - a1) * k(i1, s)
                    + y2 * (a2_new - a2) * k(i2, s)
                    + (self._b - b_old)
                )

            # if i1 or i2 is non-bound, update their error value to zero
            if self._is_unbound(i1):
                self._error[i1] = 0
            if self._is_unbound(i2):
                self._error[i2] = 0