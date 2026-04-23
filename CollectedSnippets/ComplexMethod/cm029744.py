def binomialvariate(self, n=1, p=0.5):
        """Binomial random variable.

        Gives the number of successes for *n* independent trials
        with the probability of success in each trial being *p*:

            sum(random() < p for i in range(n))

        Returns an integer in the range:

            0 <= X <= n

        The integer is chosen with the probability:

            P(X == k) = math.comb(n, k) * p ** k * (1 - p) ** (n - k)

        The mean (expected value) and variance of the random variable are:

            E[X] = n * p
            Var[X] = n * p * (1 - p)

        """
        # Error check inputs and handle edge cases
        if n < 0:
            raise ValueError("n must be non-negative")
        if p <= 0.0 or p >= 1.0:
            if p == 0.0:
                return 0
            if p == 1.0:
                return n
            raise ValueError("p must be in the range 0.0 <= p <= 1.0")

        random = self.random

        # Fast path for a common case
        if n == 1:
            return _index(random() < p)

        # Exploit symmetry to establish:  p <= 0.5
        if p > 0.5:
            return n - self.binomialvariate(n, 1.0 - p)

        if n * p < 10.0:
            # BG: Geometric method by Devroye with running time of O(np).
            # https://dl.acm.org/doi/pdf/10.1145/42372.42381
            x = y = 0
            c = _log2(1.0 - p)
            if not c:
                return x
            while True:
                y += _floor(_log2(random()) / c) + 1
                if y > n:
                    return x
                x += 1

        # BTRS: Transformed rejection with squeeze method by Wolfgang Hörmann
        # https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.47.8407&rep=rep1&type=pdf
        assert n*p >= 10.0 and p <= 0.5

        setup_complete = False
        spq = _sqrt(n * p * (1.0 - p))  # Standard deviation of the distribution
        b = 1.15 + 2.53 * spq
        a = -0.0873 + 0.0248 * b + 0.01 * p
        c = n * p + 0.5
        vr = 0.92 - 4.2 / b

        while True:

            u = random()
            u -= 0.5
            us = 0.5 - _fabs(u)
            k = _floor((2.0 * a / us + b) * u + c)
            if k < 0 or k > n:
                continue
            v = random()

            # The early-out "squeeze" test substantially reduces
            # the number of acceptance condition evaluations.
            if us >= 0.07 and v <= vr:
                return k

            if not setup_complete:
                alpha = (2.83 + 5.1 / b) * spq
                lpq = _log(p / (1.0 - p))
                m = _floor((n + 1) * p)         # Mode of the distribution
                h = _lgamma(m + 1) + _lgamma(n - m + 1)
                setup_complete = True           # Only needs to be done once

            # Acceptance-rejection test.
            # Note, the original paper erroneously omits the call to log(v)
            # when comparing to the log of the rescaled binomial distribution.
            v *= alpha / (a / (us * us) + b)
            if _log(v) <= h - _lgamma(k + 1) - _lgamma(n - k + 1) + (k - m) * lpq:
                return k