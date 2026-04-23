def gammavariate(self, alpha, beta):
        """Gamma distribution.  Not the gamma function!

        Conditions on the parameters are alpha > 0 and beta > 0.

        The probability distribution function is:

                    x ** (alpha - 1) * math.exp(-x / beta)
          pdf(x) =  --------------------------------------
                      math.gamma(alpha) * beta ** alpha

        The mean (expected value) and variance of the random variable are:

            E[X] = alpha * beta
            Var[X] = alpha * beta ** 2

        """

        # Warning: a few older sources define the gamma distribution in terms
        # of alpha > -1.0
        if alpha <= 0.0 or beta <= 0.0:
            raise ValueError('gammavariate: alpha and beta must be > 0.0')

        random = self.random
        if alpha > 1.0:

            # Uses R.C.H. Cheng, "The generation of Gamma
            # variables with non-integral shape parameters",
            # Applied Statistics, (1977), 26, No. 1, p71-74

            ainv = _sqrt(2.0 * alpha - 1.0)
            bbb = alpha - LOG4
            ccc = alpha + ainv

            while True:
                u1 = random()
                if not 1e-7 < u1 < 0.9999999:
                    continue
                u2 = 1.0 - random()
                v = _log(u1 / (1.0 - u1)) / ainv
                x = alpha * _exp(v)
                z = u1 * u1 * u2
                r = bbb + ccc * v - x
                if r + SG_MAGICCONST - 4.5 * z >= 0.0 or r >= _log(z):
                    return x * beta

        elif alpha == 1.0:
            # expovariate(1/beta)
            return -_log(1.0 - random()) * beta

        else:
            # alpha is between 0 and 1 (exclusive)
            # Uses ALGORITHM GS of Statistical Computing - Kennedy & Gentle
            while True:
                u = random()
                b = (_e + alpha) / _e
                p = b * u
                if p <= 1.0:
                    x = p ** (1.0 / alpha)
                else:
                    x = -_log((b - p) / alpha)
                u1 = random()
                if p > 1.0:
                    if u1 <= x ** (alpha - 1.0):
                        break
                elif u1 <= _exp(-x):
                    break
            return x * beta