def test_aware_compare(self):
        cls = self.theclass

        # Ensure that utcoffset() gets ignored if the comparands have
        # the same tzinfo member.
        class OperandDependentOffset(tzinfo):
            def utcoffset(self, t):
                if t.minute < 10:
                    # d0 and d1 equal after adjustment
                    return timedelta(minutes=t.minute)
                else:
                    # d2 off in the weeds
                    return timedelta(minutes=59)

        base = cls(8, 9, 10, tzinfo=OperandDependentOffset())
        d0 = base.replace(minute=3)
        d1 = base.replace(minute=9)
        d2 = base.replace(minute=11)
        for x in d0, d1, d2:
            for y in d0, d1, d2:
                for op in lt, le, gt, ge, eq, ne:
                    got = op(x, y)
                    expected = op(x.minute, y.minute)
                    self.assertEqual(got, expected)

        # However, if they're different members, uctoffset is not ignored.
        # Note that a time can't actually have an operand-dependent offset,
        # though (and time.utcoffset() passes None to tzinfo.utcoffset()),
        # so skip this test for time.
        if cls is not time:
            d0 = base.replace(minute=3, tzinfo=OperandDependentOffset())
            d1 = base.replace(minute=9, tzinfo=OperandDependentOffset())
            d2 = base.replace(minute=11, tzinfo=OperandDependentOffset())
            for x in d0, d1, d2:
                for y in d0, d1, d2:
                    got = (x > y) - (x < y)
                    if (x is d0 or x is d1) and (y is d0 or y is d1):
                        expected = 0
                    elif x is y is d2:
                        expected = 0
                    elif x is d2:
                        expected = -1
                    else:
                        self.assertIs(y, d2)
                        expected = 1
                    self.assertEqual(got, expected)