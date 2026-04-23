def test_aware_subtract(self):
        cls = self.theclass

        # Ensure that utcoffset() is ignored when the operands have the
        # same tzinfo member.
        class OperandDependentOffset(tzinfo):
            def utcoffset(self, t):
                if t.minute < 10:
                    # d0 and d1 equal after adjustment
                    return timedelta(minutes=t.minute)
                else:
                    # d2 off in the weeds
                    return timedelta(minutes=59)

        base = cls(8, 9, 10, 11, 12, 13, 14, tzinfo=OperandDependentOffset())
        d0 = base.replace(minute=3)
        d1 = base.replace(minute=9)
        d2 = base.replace(minute=11)
        for x in d0, d1, d2:
            for y in d0, d1, d2:
                got = x - y
                expected = timedelta(minutes=x.minute - y.minute)
                self.assertEqual(got, expected)

        # OTOH, if the tzinfo members are distinct, utcoffsets aren't
        # ignored.
        base = cls(8, 9, 10, 11, 12, 13, 14)
        d0 = base.replace(minute=3, tzinfo=OperandDependentOffset())
        d1 = base.replace(minute=9, tzinfo=OperandDependentOffset())
        d2 = base.replace(minute=11, tzinfo=OperandDependentOffset())
        for x in d0, d1, d2:
            for y in d0, d1, d2:
                got = x - y
                if (x is d0 or x is d1) and (y is d0 or y is d1):
                    expected = timedelta(0)
                elif x is y is d2:
                    expected = timedelta(0)
                elif x is d2:
                    expected = timedelta(minutes=(11-59)-0)
                else:
                    self.assertIs(y, d2)
                    expected = timedelta(minutes=0-(11-59))
                self.assertEqual(got, expected)