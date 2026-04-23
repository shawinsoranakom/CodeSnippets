def __init__(self, value, min_dp=None, max_dp=None):
        if min_dp is None and max_dp is None:
            self.min_dp = 2
            self.max_dp = 2
            return
        if min_dp is None and max_dp is not None:
            self.min_dp = self.max_dp = max_dp
            return
        if min_dp is not None and max_dp is None:
            # Determine the most suitable max_dp.
            # We want 180.74999999999997 to compute a max_dp of 2 but 0.01110515963896 to stay with the full number of decimals.
            max_dp = max(len(str(float(value or 0.0)).split('.')[1]), min_dp)
            while True:
                if max_dp == min_dp:
                    break
                if not float_is_zero(round(value, max_dp - 1) - value, precision_digits=11):
                    break
                max_dp = max_dp - 1

        self.min_dp = min_dp
        self.max_dp = max_dp