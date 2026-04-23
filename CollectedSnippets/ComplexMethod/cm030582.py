def test_context_subclassing(self):
        decimal = self.decimal
        Decimal = decimal.Decimal
        Context = decimal.Context
        Clamped = decimal.Clamped
        DivisionByZero = decimal.DivisionByZero
        Inexact = decimal.Inexact
        Overflow = decimal.Overflow
        Rounded = decimal.Rounded
        Subnormal = decimal.Subnormal
        Underflow = decimal.Underflow
        InvalidOperation = decimal.InvalidOperation

        class MyContext(Context):
            def __init__(self, prec=None, rounding=None, Emin=None, Emax=None,
                               capitals=None, clamp=None, flags=None,
                               traps=None):
                Context.__init__(self)
                if prec is not None:
                    self.prec = prec
                if rounding is not None:
                    self.rounding = rounding
                if Emin is not None:
                    self.Emin = Emin
                if Emax is not None:
                    self.Emax = Emax
                if capitals is not None:
                    self.capitals = capitals
                if clamp is not None:
                    self.clamp = clamp
                if flags is not None:
                    if isinstance(flags, list):
                        flags = {v:(v in flags) for v in OrderedSignals[decimal] + flags}
                    self.flags = flags
                if traps is not None:
                    if isinstance(traps, list):
                        traps = {v:(v in traps) for v in OrderedSignals[decimal] + traps}
                    self.traps = traps

        c = Context()
        d = MyContext()
        for attr in ('prec', 'rounding', 'Emin', 'Emax', 'capitals', 'clamp',
                     'flags', 'traps'):
            self.assertEqual(getattr(c, attr), getattr(d, attr))

        # prec
        self.assertRaises(ValueError, MyContext, **{'prec':-1})
        c = MyContext(prec=1)
        self.assertEqual(c.prec, 1)
        self.assertRaises(InvalidOperation, c.quantize, Decimal('9e2'), 0)

        # rounding
        self.assertRaises(TypeError, MyContext, **{'rounding':'XYZ'})
        c = MyContext(rounding=ROUND_DOWN, prec=1)
        self.assertEqual(c.rounding, ROUND_DOWN)
        self.assertEqual(c.plus(Decimal('9.9')), 9)

        # Emin
        self.assertRaises(ValueError, MyContext, **{'Emin':5})
        c = MyContext(Emin=-1, prec=1)
        self.assertEqual(c.Emin, -1)
        x = c.add(Decimal('1e-99'), Decimal('2.234e-2000'))
        self.assertEqual(x, Decimal('0.0'))
        for signal in (Inexact, Underflow, Subnormal, Rounded, Clamped):
            self.assertTrue(c.flags[signal])

        # Emax
        self.assertRaises(ValueError, MyContext, **{'Emax':-1})
        c = MyContext(Emax=1, prec=1)
        self.assertEqual(c.Emax, 1)
        self.assertRaises(Overflow, c.add, Decimal('1e99'), Decimal('2.234e2000'))
        if self.decimal == C:
            for signal in (Inexact, Overflow, Rounded):
                self.assertTrue(c.flags[signal])

        # capitals
        self.assertRaises(ValueError, MyContext, **{'capitals':-1})
        c = MyContext(capitals=0)
        self.assertEqual(c.capitals, 0)
        x = c.create_decimal('1E222')
        self.assertEqual(c.to_sci_string(x), '1e+222')

        # clamp
        self.assertRaises(ValueError, MyContext, **{'clamp':2})
        c = MyContext(clamp=1, Emax=99)
        self.assertEqual(c.clamp, 1)
        x = c.plus(Decimal('1e99'))
        self.assertEqual(str(x), '1.000000000000000000000000000E+99')

        # flags
        self.assertRaises(TypeError, MyContext, **{'flags':'XYZ'})
        c = MyContext(flags=[Rounded, DivisionByZero])
        for signal in (Rounded, DivisionByZero):
            self.assertTrue(c.flags[signal])
        c.clear_flags()
        for signal in OrderedSignals[decimal]:
            self.assertFalse(c.flags[signal])

        # traps
        self.assertRaises(TypeError, MyContext, **{'traps':'XYZ'})
        c = MyContext(traps=[Rounded, DivisionByZero])
        for signal in (Rounded, DivisionByZero):
            self.assertTrue(c.traps[signal])
        c.clear_traps()
        for signal in OrderedSignals[decimal]:
            self.assertFalse(c.traps[signal])