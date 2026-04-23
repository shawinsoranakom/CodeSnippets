def _get_new_alpha(self, i1, i2, a1, a2, e1, e2, y1, y2):
        k = self._k
        if i1 == i2:
            return None, None

        # calculate L and H which bound the new alpha2
        s = y1 * y2
        if s == -1:
            l, h = max(0.0, a2 - a1), min(self._c, self._c + a2 - a1)  # noqa: E741
        else:
            l, h = max(0.0, a2 + a1 - self._c), min(self._c, a2 + a1)  # noqa: E741
        if l == h:
            return None, None

        # calculate eta
        k11 = k(i1, i1)
        k22 = k(i2, i2)
        k12 = k(i1, i2)

        # select the new alpha2 which could achieve the minimal objectives
        if (eta := k11 + k22 - 2.0 * k12) > 0.0:
            a2_new_unc = a2 + (y2 * (e1 - e2)) / eta
            # a2_new has a boundary
            if a2_new_unc >= h:
                a2_new = h
            elif a2_new_unc <= l:
                a2_new = l
            else:
                a2_new = a2_new_unc
        else:
            b = self._b
            l1 = a1 + s * (a2 - l)
            h1 = a1 + s * (a2 - h)

            # Method 1
            f1 = y1 * (e1 + b) - a1 * k(i1, i1) - s * a2 * k(i1, i2)
            f2 = y2 * (e2 + b) - a2 * k(i2, i2) - s * a1 * k(i1, i2)
            ol = (
                l1 * f1
                + l * f2
                + 1 / 2 * l1**2 * k(i1, i1)
                + 1 / 2 * l**2 * k(i2, i2)
                + s * l * l1 * k(i1, i2)
            )
            oh = (
                h1 * f1
                + h * f2
                + 1 / 2 * h1**2 * k(i1, i1)
                + 1 / 2 * h**2 * k(i2, i2)
                + s * h * h1 * k(i1, i2)
            )
            """
            Method 2: Use objective function to check which alpha2_new could achieve the
            minimal objectives
            """
            if ol < (oh - self._eps):
                a2_new = l
            elif ol > oh + self._eps:
                a2_new = h
            else:
                a2_new = a2

        # a1_new has a boundary too
        a1_new = a1 + s * (a2 - a2_new)
        if a1_new < 0:
            a2_new += s * a1_new
            a1_new = 0
        if a1_new > self._c:
            a2_new += s * (a1_new - self._c)
            a1_new = self._c

        return a1_new, a2_new