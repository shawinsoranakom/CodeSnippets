def test_nan_comparisons(self):
        # comparisons involving signaling nans signal InvalidOperation

        # order comparisons (<, <=, >, >=) involving only quiet nans
        # also signal InvalidOperation

        # equality comparisons (==, !=) involving only quiet nans
        # don't signal, but return False or True respectively.
        Decimal = self.decimal.Decimal
        InvalidOperation = self.decimal.InvalidOperation
        localcontext = self.decimal.localcontext

        n = Decimal('NaN')
        s = Decimal('sNaN')
        i = Decimal('Inf')
        f = Decimal('2')

        qnan_pairs = (n, n), (n, i), (i, n), (n, f), (f, n)
        snan_pairs = (s, n), (n, s), (s, i), (i, s), (s, f), (f, s), (s, s)
        order_ops = operator.lt, operator.le, operator.gt, operator.ge
        equality_ops = operator.eq, operator.ne

        # results when InvalidOperation is not trapped
        with localcontext() as ctx:
            ctx.traps[InvalidOperation] = 0

            for x, y in qnan_pairs + snan_pairs:
                for op in order_ops + equality_ops:
                    got = op(x, y)
                    expected = True if op is operator.ne else False
                    self.assertIs(expected, got,
                                "expected {0!r} for operator.{1}({2!r}, {3!r}); "
                                "got {4!r}".format(
                            expected, op.__name__, x, y, got))

        # repeat the above, but this time trap the InvalidOperation
        with localcontext() as ctx:
            ctx.traps[InvalidOperation] = 1

            for x, y in qnan_pairs:
                for op in equality_ops:
                    got = op(x, y)
                    expected = True if op is operator.ne else False
                    self.assertIs(expected, got,
                                  "expected {0!r} for "
                                  "operator.{1}({2!r}, {3!r}); "
                                  "got {4!r}".format(
                            expected, op.__name__, x, y, got))

            for x, y in snan_pairs:
                for op in equality_ops:
                    self.assertRaises(InvalidOperation, operator.eq, x, y)
                    self.assertRaises(InvalidOperation, operator.ne, x, y)

            for x, y in qnan_pairs + snan_pairs:
                for op in order_ops:
                    self.assertRaises(InvalidOperation, op, x, y)