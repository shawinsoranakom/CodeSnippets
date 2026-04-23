def rounding_direction(self, x, mode):
        """Determine the effective direction of the rounding when
           the exact result x is rounded according to mode.
           Return -1 for downwards, 0 for undirected, 1 for upwards,
           2 for ROUND_05UP."""
        cmp = 1 if x.compare_total(P.Decimal("+0")) >= 0 else -1

        if mode in (P.ROUND_HALF_EVEN, P.ROUND_HALF_UP, P.ROUND_HALF_DOWN):
            return 0
        elif mode == P.ROUND_CEILING:
            return 1
        elif mode == P.ROUND_FLOOR:
            return -1
        elif mode == P.ROUND_UP:
            return cmp
        elif mode == P.ROUND_DOWN:
            return -cmp
        elif mode == P.ROUND_05UP:
            return 2
        else:
            raise ValueError("Unexpected rounding mode: %s" % mode)